import os

SQLDEF = "localhost:5432"
SQLHOST = os.environ.get("SQLHOST",SQLDEF)
DEBUG = os.environ.get("DEBUG",True)

import json

import sqlalchemy as db
from sqlalchemy.orm import Session

from database.models import Commits, Models, Elements, Models_Elements, \
    Reqts, Verifications, Actions

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

def insert_commit_data(ref, commit, commit_date):
    c, engine = connect()
    with Session(engine) as session:
        result = session \
            .query(Commits) \
            .filter(
                Commits.ref == ref,
                Commits.commit==commit
            ) \
            .first()

        if result is None:
            print('Inserting new commit into db.')
            commit_obj = Commits(ref=ref, commit=commit, date=commit_date)
            statement = session.add(commit_obj)
            session.commit()
        else:
            print('Warning: This commit already existed.')
    c.close()
    engine.dispose()

def insert_model_data(ref, commit, models, elements):
    c, engine = connect()
    with Session(engine) as session:
        # Grab the commit id number from the DB.
        result = session \
            .query(Commits) \
            .filter(
                Commits.ref == ref,
                Commits.commit==commit
            ) \
            .first()

        if result is None:
            raise NotImplementedError('Commit Id was not found')
        else:
            commit_id = result.id

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
                        ) \
                        .first()

                    # There were no results
                    if results is None:
                        # So create a new row
                        this_me = Models_Elements(
                            model_id = m_rid,
                            element_id = e_id
                        )
                        # Add the row
                        session.add(this_me)
                        session.commit()
                ## END For each element in all elements associated with model
            ## END for each model
        ## End for each notebook

    c.close()
    engine.dispose()

def insert_req_ver_actions(ref, commit, requirements, verifications, actions):
    c, engine = connect()
    with Session(engine) as session:
        print('Grabbing the commit id.')
        result = session \
            .query(Commits) \
            .filter(
                Commits.ref == ref,
                Commits.commit==commit
            ) \
            .first()

        if result is None:
            raise NotImplementedError('Could not find commit.')
        else:
            commit_id = result.id

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
            if 'shortName' in element_payload:
                shortName = element_payload['shortName']
            else:
                shortName = None

            if 'qualifiedName' in element_payload:
                qualifiedName = element_payload['qualifiedName']
            else:
                qualifiedName = None

            this_r = Reqts(
                commit_id=commit_id,
                declaredName = requirements[e_id]['name'],
                shortName = shortName,
                qualifiedName = qualifiedName,
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
                requirement_id = results.id
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

            this_a = Actions(
                element_id = element_id,
                verifications_id = verifications_id,
                declaredName = actions[a_id]['declaredName'],
                qualifiedName = actions[a_id]['qualifiedName'],
                harbor = json.dumps(actions[a_id]['tools']['harbor']),
                artifacts = json.dumps(actions[a_id]['tools']['artifacts']),
                variables = var
            )
            session.add(this_a)
            session.commit()
    c.close()
    engine.dispose()
