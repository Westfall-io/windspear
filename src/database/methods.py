# Copyright (c) 2023-2024 Westfall Inc.
#
# This file is part of Windspear.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, and can be found in the file NOTICE inside this
# git repository.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

SQLDEF = "localhost:5432"
SQLHOST = os.environ.get("SQLHOST",SQLDEF)
DEBUG = os.environ.get("DEBUG",True)

import json

import sqlalchemy as db
from sqlalchemy.orm import Session

from database.models import Model_Repo, Commits, Models, Elements, \
    Models_Elements, Reqts, Verifications, Actions

def connect():
    db_type = "postgresql"
    user = "postgres"
    passwd = "mysecretpassword"
    address = SQLHOST
    db_name = "sysml2"

    address = db_type+"://"+user+":"+passwd+"@"+address+"/"+db_name
    engine = db.create_engine(address)
    conn = engine.connect()

    return conn, engine

def push_commit_completed(commit_id):
    c, engine = connect()
    with Session(engine) as session:
        result = session \
            .query(Commits) \
            .filter(Commits.id == commit_id) \
            .update({'processed': True})
        session.commit()
    c.close()
    engine.dispose()

def insert_commit_data(repopath, default_branch, ref, commit, commit_date):
    c, engine = connect()
    with Session(engine) as session:

        # Verify that the repo information is correct
        result = session \
            .query(Model_Repo) \
            .filter(Model_Repo.full_name == repopath) \
            .first()

        if result is None:
            total = session.query(Model_Repo.id).count()
            if total == 0:
                this_repo = Model_Repo(
                    full_name=repopath,
                    default_branch = default_branch
                )
                session.add(this_repo)
                session.commit()
            else:
                raise NotImplementedError("Too many entries in model repo database.")
        else:
            if result.default_branch != default_branch:
                session.merge(this_repo.set_default(default_branch))
                session.commit()
            else:
                pass

        result = session \
            .query(Commits.id) \
            .filter(
                Commits.ref == ref,
                Commits.commit==commit
            ) \
            .first()

        if result is None:
            print('Inserting new commit into db.')
            commit_obj = Commits(
                ref=ref,
                commit=commit,
                processed=False,
                date=commit_date)
            session.add(commit_obj)
            session.commit()
            session.refresh(commit_obj)
            cdb_id = commit_obj.id
        else:
            print('Warning: This commit already existed.')
            # Set this commit to unprocessed.
            cdb_id = result.id
            result = session \
                .query(Commits) \
                .filter(Commits.id == cdb_id) \
                .update({'processed': False})
            # Deleting in order of foreign keys
            session.query(Models_Elements) \
                .filter(
                    Models_Elements.commit_id==cdb_id
                ) \
                .delete()
            session.query(Models) \
                .filter(
                    Models.commit_id==cdb_id
                ) \
                .delete()
            session.query(Actions) \
                .filter(
                    Actions.commit_id==cdb_id
                ) \
                .delete()
            session.query(Verifications) \
                .filter(
                    Verifications.commit_id==cdb_id
                ) \
                .delete()
            session.query(Reqts) \
                .filter(
                    Reqts.commit_id==cdb_id
                ) \
                .delete()
            session.query(Elements) \
                .filter(
                    Elements.commit_id==cdb_id
                ) \
                .delete()

            session.commit()

    c.close()
    engine.dispose()
    return cdb_id

def insert_model_data(commit_id, models, elements):
    c, engine = connect()
    with Session(engine) as session:
        # Grab the commit id number from the DB.
        result = session \
            .query(Commits) \
            .filter(Commits.id == commit_id) \
            .first()

        if result is None:
            raise NotImplementedError('Commit Id was not found')

        # For each element in the full list of elements
        for e_id in elements:

            # Determine if this element has a name
            if 'declaredName' in elements[e_id]['payload']:
                name = elements[e_id]['payload']['declaredName']
            else:
                name = 'undefined'

            # Build a row for insert
            this_e = Elements(
                commit_id=commit_id,
                element_id = e_id,
                element_text = json.dumps(elements[e_id]),
                element_name = name
            )

            result = session \
                .query(Elements) \
                .filter(
                    Elements.element_id==e_id,
                    Elements.commit_id==commit_id
                ) \
                .first()

            if result == None:
                # Insert the row
                session.add(this_e)
            else:
                # Overwrite this element with this latest.
                print('Warning: This element already existed, updating with the information.')
                session.merge(this_e.set_id(result.id))
            session.commit()

        for notebook in models:
            for m_id in models[notebook]:
                # Build a row to insert
                this_m = Models(
                    commit_id=commit_id,
                    nb_id=m_id,
                    execution_order=models[notebook][m_id][0],
                    model_text=models[notebook][m_id][1],
                    model_hash=str(models[notebook][m_id][2]),
                    path_text=models[notebook][m_id][3],
                    path_hash=str(models[notebook][m_id][4]),
                    element_name=models[notebook][m_id][5]
                )

                # Check if the model exists
                result = session \
                    .query(Models) \
                    .filter(
                        Models.commit_id==commit_id,
                        Models.nb_id==m_id,
                        Models.model_hash==str(models[notebook][m_id][2]),
                        Models.path_hash==str(models[notebook][m_id][4]),
                        Models.element_name==models[notebook][m_id][5]
                    ) \
                    .first()

                if result is None:
                    # Insert the row
                    session.add(this_m)
                else:
                    # Update the row
                    session.merge(this_m.set_id(result.id))
                session.commit()

                # Grab the id for this row
                result = session \
                    .query(Models) \
                    .filter(
                        Models.commit_id==commit_id,
                        Models.nb_id==m_id,
                        Models.path_hash==str(models[notebook][m_id][4])
                    ) \
                    .first()
                m_rid = result.id

                # For each element this model is linked to
                for element in models[notebook][m_id][6]:
                    # Grab the id for this element
                    result = session \
                        .query(Elements) \
                        .filter(
                            Elements.element_id==element
                        ) \
                        .first()

                    if result is None:
                        raise NotImplementedError('Could not find element.')

                    e_id = result.id

                    # Look for a result equal to the one we need to make.
                    results = session \
                        .query(Models_Elements) \
                        .filter(
                            Models_Elements.model_id==m_rid,
                            Models_Elements.element_id==e_id,
                            Models_Elements.commit_id==commit_id,
                        ) \
                        .first()

                    # There were no results
                    if results is None:
                        # So create a new row
                        this_me = Models_Elements(
                            model_id = m_rid,
                            element_id = e_id,
                            commit_id = commit_id
                        )
                        # Add the row
                        session.add(this_me)
                        session.commit()
                ## END For each element in all elements associated with model
            ## END for each model
        ## End for each notebook

    c.close()
    engine.dispose()

def insert_req_ver_actions(commit_id, requirements, verifications, actions):
    c, engine = connect()
    with Session(engine) as session:
        print('Publishing requirements.')
        for e_id in requirements:
            result = session \
                .query(Elements) \
                .filter(
                    Elements.element_id==e_id,
                ) \
                .first()

            if result is None:
                raise NotImplementedError('Could not find this element.')

            element_payload = json.loads(result.element_text)['payload']

            this_r = Reqts(
                commit_id=commit_id,
                declaredName = requirements[e_id]['declaredName'],
                shortName = requirements[e_id]['shortName'],
                qualifiedName = requirements[e_id]['qualifiedName'],
                element_id = result.id
            )
            session.add(this_r)
            session.commit()

        print('Publishing verifications.')
        for e_id in verifications:
            results = session \
                .query(Elements) \
                .filter(
                    Elements.element_id==e_id,
                ) \
                .first()

            if results is None:
                raise NotImplementedError('Could not find this element.')

            element_id = results.id

            # This assumes we can only verify one requirement at a time.
            results = session \
                .query(Reqts) \
                .join(Elements) \
                .filter(Reqts.element_id == Elements.id) \
                .filter(
                    Elements.element_id==verifications[e_id]['requirements'][0]['@id'],
                ) \
                .first()

            if results is None:
                raise NotImplementedError('Could not find this element.')

            this_r = Verifications(
                commit_id=commit_id,
                element_id = element_id,
                requirement_id = results.id,
                attempted = None,
            )
            session.add(this_r)
            session.commit()

        print('Publishing actions.')
        for a_id in actions:
            # Get this element id
            results = session \
                .query(Elements) \
                .filter(
                    Elements.element_id==a_id,
                ) \
                .first()

            if results is None:
                raise NotImplementedError('Could not find this element.')

            element_id = results.id

            # Get this verification id
            results = session \
                .query(Verifications) \
                .join(Elements) \
                .filter(Verifications.element_id == Elements.id) \
                .filter(
                    Elements.element_id==actions[a_id]['verification'],
                ) \
                .first()

            if results is None:
                raise NotImplementedError('Could not find this element.')

            verifications_id = results.id

            if 'variables' in actions[a_id]['tools']:
                var = json.dumps(actions[a_id]['tools']['variables'])
            else:
                var = json.dumps({})

            valid = True
            if actions[a_id]['tools']['harbor'] is not None:
                harbor_uri = actions[a_id]['tools']['harbor']['uri']
            else:
                harbor_uri = None
                valid = False

            if actions[a_id]['tools']['artifacts'] is not None:
                artifacts_uri = actions[a_id]['tools']['artifacts']['uri']
            else:
                artifacts_uri = None
                valid = False

            if 'dependency' in actions[a_id]:
                result = session \
                    .query(Actions.id) \
                    .join(Elements, Actions.element_id == Elements.id) \
                    .filter(
                        Elements.element_id==actions[a_id]['dependency'],
                    ) \
                    .first()
                if result is None:
                    raise NotImplementedError('Could not find this dependency.')
                else:
                    dependency = result.id
            else:
                dependency = None

            this_a = Actions(
                commit_id = commit_id,
                element_id = element_id,
                verifications_id = verifications_id,
                shortName = actions[a_id]['shortName'],
                declaredName = actions[a_id]['declaredName'],
                qualifiedName = actions[a_id]['qualifiedName'],
                harbor = harbor_uri,
                artifacts = artifacts_uri,
                variables = var,
                valid = valid,
                dependency = dependency
            )
            session.add(this_a)
            session.commit()
        # END for actions
    # End session
    c.close()
    engine.dispose()
