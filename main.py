import time
start_time = time.time()

import os

APIDEF = "https://api.sysml.domain"
APIHOST = os.environ.get("APIHOST",APIDEF)
WINDSTORMDEF = "https://api.sysml.domain"
WINDSTORMHOST = os.environ.get("WINDSTORMHOST",WINDSTORMDEF)

DEBUG = os.environ.get("DEBUG",True)

from datetime import datetime
import dateutil

def getDateTimeFromISO8601String(s):
    d = dateutil.parser.parse(s)
    return d

import json
import uuid as uuid_lib
from pprint import pprint

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Need to ensure sos kernel installed after pip installs
## python -m sos_notebook.install
## jupyter labextension install --debug @systems-modeling/jupyterlab-sysml

import notebook.methods as nb_func
import gitrepo.methods as gitrepo
import database.methods as database

def main(ref, commit, repopath):
    if ref == '':
        ref='refs/heads/main'
    if commit == '':
        commit='edf03b95f6f612de4bea9286418020f5beea74a6'
    if repopath == '':
        repopath='gitea_admin/test_workflow'
    # Download repo and set to correct branch
    # Grab commits on this branch and dates
    # Then set to commit in webhook
    dir_path, branch, commit_data = gitrepo.checkout_branch_commit(
        ref, commit, repopath)

    # Get date for this commit
    for sublist in commit_data:
        if sublist[1] == commit:
            commit_date = sublist[0]
            break
    #print(commit_data)
    #print(commit_date, type(commit_date))

    ##### Commit to DB - Commits:
    ## ref, commit, date
    database.insert_commit_data(
        ref.split('/')[-1],
        commit,
        getDateTimeFromISO8601String(commit_date)
    )

    # Create a new project in the standard sysml repo
    timestamp = datetime.now()
    project_name = f"Digital Forge Project - {timestamp}"
    project_data = {
      "@type":"Project",
      "name": project_name,
      "description": "Auto-generated project from git repo."
    }

    project_post_url = f"{APIHOST}/projects"

    #project_post_response = requests.post(project_post_url,
    #  headers={"Content-Type": "application/json"},
    #  data=json.dumps(project_data),
    #  verify=False)

    #if project_post_response.status_code == 200:
    #    project_response_json = project_post_response.json()
    #    pprint(project_response_json)
    #    pid = project_response_json['@c.commit']
    #else:
    #    pprint(f"Problem in creating a new project at {timestamp}")
    #    pprint(project_post_response)
    #    raise

    # Grab all models from the commit
    models, elements = nb_func.search_models(dir_path, DEBUG=DEBUG)
    # Output from this commit is a dictionary
    # models with structure:
    # models[notebook_path][notebook_id] = [
    #   model_execution_number,
    #   model_text,
    #   model_hash,
    #   path_text,
    #   path_hash,
    #   element_name,
    #   all_element_ids,
    #   new_element_ids,
    # ]

    ##### Commit to DB - Models:
    ## commit_idFK, nb_id, model_execution_number, model_text, model_hash,
    ## path_text, path_hash, element_name
    database.insert_model_data(ref.split('/')[-1], commit, models, elements)

    ##### Commit to DB - Elements:
    ## For element in elements:
    ## element_id, element_name, element_text

    ##### Commit to DB - Model_Elements:
    ## For model in models:
    ##   For element in all_elements:
    ## model_id, element_id

    requirements, verifications, actions = nb_func.parse_models(models, elements)

    database.insert_req_ver_actions(ref.split('/')[-1], commit, requirements, verifications, actions)

    #requests.post(WINDSTORMHOST, json={'ref'=ref, 'commit':commit})

if __name__ == '__main__':
    if DEBUG:
        import shutil
        if os.path.exists('sysml_workflow'):
            shutil.rmtree('sysml_workflow')
        if os.path.exists('tmp'):
            shutil.rmtree('tmp')

    import fire
    fire.Fire(main)
    print("--- %s seconds ---" % (time.time() - start_time))
