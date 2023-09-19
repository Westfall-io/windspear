import time
start_time = time.time()

import os

APIDEF = "https://api.sysml.domain"
APIHOST = os.environ.get("APIHOST",APIDEF)

import json
import uuid as uuid_lib
from pprint import pprint

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Need to ensure sos kernel installed after pip installs
## python -m sos_notebook.install
## jupyter labextension install --debug @systems-modeling/jupyterlab-sysml

import notebook.methods as notebook
import gitrepo.methods as gitrepo
import database.methods as database

def main(ref, commit, repopath):
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
    #print(commit_date)

    # Create a new project in the standard sysml repo
    project_name = branch+"_"+commit
    import sysml_v2_api_client
    from sysml_v2_api_client.rest import ApiException
    configuration = sysml_v2_api_client.Configuration(
        host = APIHOST
    )

    with sysml_v2_api_client.ApiClient(configuration) as api_client:
        api_instance = sysml_v2_api_client.ProjectApi(api_client)

        #print("Getting all projects in the database.")
        #try:
        #    api_response = api_instance.get_projects(page_size=10)
        #    pids = []
        #    for proj in api_response:
        #        pids.append(proj.id)

        #except ApiException as e:
        #    print("Exception when calling ProjectApi->get_projects: %s\n" % e)

        #print("Deleting all projects found.")
        #for pid in pids:
        #    try:
                # Delete project by ID
        #        print("  Deleting project: {}".format(pid))
        #        api_response = api_instance.delete_project_by_id(pid)
        #        pprint(api_response)
        #    except ApiException as e:
        #        print("Exception when calling ProjectApi->delete_project_by_id: %s\n" % e)
        #        raise
        proj = sysml_v2_api_client.Project(name=project_name)

        print('Adding this new project.')
        try:
            # Create project
            api_response = api_instance.post_project(body=proj)
            pid = api_response.id
            bid = api_response.default_branch.id

        except ApiException as e:
            print("Exception when calling ProjectApi->post_project: %s\n" % e)
            raise ApiException

    # Grab all models from the commit
    models = notebook.search_models(dir_path)
    # Output from this commit is a dictionary
    # models[nb_id] = [model_text, model_hash, path_hash, name, elementAPIJSON]

    model_waves = [[],[],[]]
    model = {}
    for nb_id in models:
        dataversion = models[nb_id][4]
        if dataversion != '':
            # There is a model, get the model
            elements = json.loads(dataversion)
            for element in elements:
                with open('tmp/'+element['identity']['@id']+'.json', 'w') as f:
                    json.dump(element, f, indent=3)
                waves_added = 0
                # Grab the payload as string
                payload = element['payload'].copy()
                model[element['identity']['@id']] = payload
                element['payload_old'] = payload
                # Make a dictionary of a single level output with all sublevels as str
                saved_keys = []
                dropped_keys = []
                for key in payload.keys():
                    # For each key in this payload
                    if '@id' in json.dumps(payload[key]):
                        # If this text is in it, pop it from the dictionary
                        dropped_keys.append(key)
                    else:
                        saved_keys.append(key)

                element['payload'] = dict((key,value) for key, value \
                    in payload.items() if key in saved_keys)
                element['payload']['@type'] = payload['@type']
                # Now load it and write to file
                if isinstance(element['payload']['@type'], str):
                    #
                    # This model isn't linked to another by type, submit it in wave 1
                    model_waves[0].append(element.copy())
                    waves_added += 1
                else:
                    # This model is linked to a different type, submit it in wave 2
                    model_waves[1].append(element.copy())
                    waves_added += 1

                # Submit all dropped keys in wave 3 after all elements are made
                element['payload'] = dict((key,value) for key, value \
                    in payload.items() if key in dropped_keys)
                element['payload']['@type'] = payload['@type']
                if len(element['payload'].keys()) > 0:
                    model_waves[2].append(element.copy())
                    waves_added += 1

                if waves_added == 0:
                    print(payload)
                    raise

    commit_id = None
    commit_post_url = f"{APIHOST}/projects/{pid}/commits"

    for wave in model_waves:
        print('Starting wave.')
        for element in wave:
            # Make a dataversion element
            #print(element)
            dv = {}
            dv['@type'] = 'DataVersion'
            dv['payload'] = element['payload']
            dv['identity'] = element['identity']
            # Make a commit element
            body = {}
            body['change'] = [dv]
            body['@type'] = 'Commit'
            if commit_id is not None:
                body["previousCommit"] = {
                    "@id": commit_id
                }

            commit_post_response = requests.post(commit_post_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(body),
                verify=False)

            if commit_post_response.status_code == 200:
                commit_response_json = commit_post_response.json()
                #pprint(commit_response_json)
                commit_id = commit_response_json['@id']
            else:
                commit_response_json = commit_post_response.json()
                #pprint(commit_response_json)
                with open('tmp/file.json', 'w') as f:
                    json.dump(element,f,indent=3)
                raise

    #_, engine = database.connect()

def unused():
    # Collect all elements from each notebook
    change = {}
    for nb_id in models:
        if models[nb_id][4] != '':
            # This model has data, load it in

            # Path hash to a notebook
            pathhash = models[nb_id][2]
            # Changes for this notebook, don't overwrite
            if not pathhash in change:
                change[pathhash] = []

            try:
                elements = json.loads(models[nb_id][4])
                change[pathhash].extend(elements)
            except json.JSONDecodeError:
                print(models[nb_id])
                raise json.JSONDecodeError
        else:
            # This was probably not proper SysML
            continue

    # Brute force add all of the elements to the API
    commit_id = None
    commit_post_url = f"{APIHOST}/projects/{pid}/commits"
    for pathhash in change:
        # Submit all elements without @id, these have no outgoing edges
        elements = change[pathhash]
        data = []
        elements_submitted = 0
        for element in elements:
            # Make a dataversion element
            dv = {}
            dv['@type'] = 'DataVersion'
            dv['payload'] = element['payload']
            dv['identity'] = element['identity']

            if '@id' in json.dumps(element['payload']):
                # Skip creation of these which will fail the first time around
                data.append(dv)
            else:
                body = {}
                body['change'] = [dv]
                body['@type'] = 'Commit'
                if commit_id is not None:
                    body["previousCommit"] = {
                        "@id": commit_id
                    }

                commit_post_response = requests.post(commit_post_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(body),
                    verify=False)

                if commit_post_response.status_code == 200:
                    elements_submitted += 1
                    commit_response_json = commit_post_response.json()
                    #pprint(commit_response_json)
                    commit_id = commit_response_json['@id']
                else:
                    raise ValueError('This element could not be submitted')

        total_elements = len(elements)
        print('Submitted {} elements of {}.'.format(elements_submitted, total_elements))
        elements_submitted_last = elements_submitted - 1
        while elements_submitted < total_elements \
            and elements_submitted > elements_submitted_last:
            # Init
            elements_submitted_last = elements_submitted
            data2 = []
            for dv in data:
                body = {}
                body['change'] = [dv]
                body['@type'] = 'Commit'
                if commit_id is not None:
                    body["previousCommit"] = {
                        "@id": commit_id
                    }

                commit_post_response = requests.post(commit_post_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(body),
                    verify=False)

                if commit_post_response.status_code == 200:
                    elements_submitted += 1
                    commit_response_json = commit_post_response.json()
                    #pprint(commit_response_json)
                    commit_id = commit_response_json['@id']
                else:
                    data2.append(dv)
                    commit_response_json = commit_post_response.json()
                    pprint(commit_response_json)
                    with open('tmp/file.json', 'w') as f:
                        json.dump(body,f,indent=3)
                    raise

            print('Submitted {} elements of {}.'.format(elements_submitted, total_elements))
            # Pop all of the previous elements
            data = data2
            if len(data)==total_elements-elements_submitted:
                continue
            else:
                raise ValueError('Leftover {} elements and should have {}.'.format(len(data), total_elements-elements_submitted))

        if elements_submitted == total_elements:
            print('Complete in building elements')
        else:
            print('Failed to submit all elements')
            raise ValueError

if __name__ == '__main__':
    import fire
    fire.Fire(main)
    print("--- %s seconds ---" % (time.time() - start_time))
