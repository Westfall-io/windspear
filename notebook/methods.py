import os
import json
import base64
import hashlib
import uuid as uuid_lib

import papermill as pm

def hash(string):
    return int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16)

def _base_nb():
    return {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "SoS",
                "language": "sos",
                "name": "sos"
            },
            "language_info": {
                "codemirror_mode": "sos",
                "file_extension": ".sos",
                "mimetype": "text/x-sos",
                "name": "sos",
                "nbconvert_exporter": \
                    "sos_notebook.converter.SoS_Exporter",
                "pygments_lexer": "sos"
            },
            "sos": {
                "kernels": [
                    [
                        "Python3",
                        "python3",
                        "Python3",
                        "#FFD91A",
                        {
                            "name": "ipython",
                            "version": 3
                        }
                    ],
                    [
                        "SoS",
                        "sos",
                        "",
                        "",
                        "sos"
                    ],
                    [
                        "SysML",
                        "sysml",
                        "sysml",
                        "",
                        "sysml"
                    ]
                ],
                "version": "0.24.2",
                }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def _make_nb_cell(model,tags=[]):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": model[0],
        "metadata": {
            "kernel": "SysML",
            "tags": tags
        },
        "outputs": [],
        "source": [model[1]]
    }

def search_models(dir_path):
    # Search for models
    all_models = {}
    languages = ["sos", "SysML"]
    # Iterate directory
    for (dir_path, dir_names, file_names) in os.walk(dir_path):
        for name in file_names:
            if name.endswith('.ipynb'):
                models = []
                print('Notebook found: {}'.format(name))
                path = os.path.join(dir_path, name)
                with open(path, 'r') as f:
                    nb = json.loads(f.read())
                    if nb["metadata"]["kernelspec"]["language"] in languages:
                        for cell in nb["cells"]:
                            if cell["metadata"]["kernel"] == "SysML":
                                model_text = "".join(
                                    filter(
                                        lambda x : not x.startswith("%"),
                                        cell["source"]
                                    )
                                )
                                # Skip this model if it's now empty
                                if model_text.replace("\n","") == "":
                                    continue
                                print('Found model.')
                                model_id = cell["id"]
                                model_hash = str(hash(model_text))
                                path_hash = str(hash(os.path.join(dir_path, name)))
                                models.append([model_id, model_text, model_hash, path_hash, '', ''])
                                #print('-------------\n',model_text)

                            ## End found a cell that's SysML
                        ## End for cell in cells
                    ## End check if notebook has any SysML
                ## End open file
                all_models.update({model[0]:model[1:] for model in models})

                if len(models) > 0:
                    # Put all the SysML in a new notebook
                    new_nb = _base_nb()
                    cells = []
                    for model in models:
                        cells.append(_make_nb_cell(model))
                    new_nb["cells"] = cells
                    temp_file = '_sysml_windspear.ipynb'
                    with open(temp_file, 'w') as f:
                        f.write(json.dumps(new_nb))
                    pm.execute_notebook(temp_file,temp_file,kernel_name="sysml")
                    obj_names = []
                    with open(temp_file, 'r') as f:
                        # Read the notebook again
                        nb = json.loads(f.read())
                        for cell in nb["cells"]:
                            # Check for the SysML cells
                            if cell["metadata"]["kernel"] == "SysML":
                                # Find the output which must exist now
                                for out in cell["outputs"]:
                                    # Find the right output to continue
                                    if "data" in out.keys():
                                        if "text/plain" in out["data"]:
                                            id_cell = cell["id"]
                                            names = out["data"]["text/plain"]
                                            for name in names:
                                                obj_name = "".join(
                                                    name.split("(")[0]
                                                        .split(" ")[1:]
                                                )
                                                if obj_name[0] == "<":
                                                    obj_name = obj_name[obj_name.find(">")+1:]
                                                if obj_name != '':
                                                    obj_names.append([id_cell, obj_name])
                                        else:
                                            print(models)
                                            print(cell["source"])
                                            #print(out["data"])
                                            raise ValueError
                                            ## End if valid name, otherwise can't export
                                        ## End for name
                                    ## End check correct data output
                                ## End for each cell output
                            ## End this cell is SysML
                        ## End for each cell
                    ## Close file
                    for obj_name in obj_names:
                        cells.append(
                            _make_nb_cell(
                                [
                                    str(uuid_lib.uuid4()),
                                    "%export "+obj_name[1]
                                ],
                                tags = [obj_name[0]]
                            )
                        )
                        #cells.append(
                        #    _make_nb_cell(
                        #        [
                        #            str(uuid_lib.uuid4()),
                        #            "%publish "+obj_name[1]
                        #        ],
                        #        tags = [obj_name[0]]
                        #    )
                        #)
                    new_nb["cells"] = cells
                    with open(temp_file, 'w') as f:
                        f.write(json.dumps(new_nb))
                    pm.execute_notebook(temp_file,temp_file,kernel_name="sysml")

                    with open(temp_file, 'r') as f:
                        # Read the notebook again
                        nb = json.loads(f.read())
                        for cell in nb["cells"]:
                            # Check for the SysML cells
                            if cell["metadata"]["kernel"] == "SysML":
                                # Find the output which must exist now
                                for out in cell["outputs"]:
                                    # Find the right output to continue
                                    if "data" in out.keys():
                                        if "text/html" in out["data"]:
                                            html = out["data"]["text/html"][0]
                                            data = json.loads(base64.b64decode(html[html.find('href=')+35:-14]))
                                            #print(json.dumps(data, sort_keys=True, indent=10))
                                            name = cell["source"][0][8:]
                                            id_cell = cell["metadata"]["tags"][0]
                                            all_models[id_cell][3] = name
                                            all_models[id_cell][4] = json.dumps(data)
                                            ## End if valid name, otherwise can't export
                                        ## End for name
                                    ## End check correct data output
                                ## End for each cell output
                            ## End this cell is SysML
                        ## End for each cell
                    ## Close file
            ## End check if correct file type
        ## End for file in files

    return all_models
