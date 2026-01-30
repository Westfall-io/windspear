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

from env import *

import json
import base64
import hashlib
import uuid as uuid_lib

from queue import PriorityQueue

import papermill as pm

from notebook.models import Elements, Element
from notebook.jupyter import _base_nb, _make_nb_cell
from notebook.action import add_stored_data
from notebook.sysml import handle_literals, handle_feature_chain

# notebook/methods.py: Core routines to discover, execute, and parse SysML
# models embedded in Jupyter notebooks. This module drives the notebook
# execution (via `papermill`), decodes exported element JSON, and walks
# the exported structures to build normalized `requirements`,
# `verifications`, and `actions` dictionaries for persistence.

def hash(string):
    # Compute a stable integer hash for the given string using MD5.
    return int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16)

def search_models(dir_path, DEBUG=False):
    """Discover and execute SysML model cells inside notebooks.

    Walk `dir_path` looking for `.ipynb` files that use the SysML (or
    `sos`) kernel. For each notebook this function:
        - extracts SysML code cells (ignoring magic lines starting with `%`),
        - builds a temporary notebook containing only those cells,
        - executes the temporary notebook with `papermill` (kernel `sysml`) so
            that exported model elements are produced in the cell outputs,
        - decodes the exported JSON (base64 embedded in HTML output) and
            attaches exported element payloads to the corresponding model entry.

    Returns a tuple (valid_models, all_elements) where `valid_models` maps
    notebook filenames to the parsed models that successfully exported
    element JSON, and `all_elements` is a dictionary of all exported element
    objects keyed by their element id.
    """
    # Search for models
    all_models = {}
    # Notebook kernels we care about (SysML and optional sos interoperability)
    languages = ["sos", "SysML"]
    
    # Iterate directory
    for (dir_path, dir_names, file_names) in os.walk(dir_path):
        for name in file_names:
            if name.endswith('.ipynb'):
                models = {}
                model_num = 0

                ## Parse Notebook for models
                print('Notebook found: {}'.format(name))
                path = os.path.join(dir_path, name)
                with open(path, 'r') as f:
                    nb = json.loads(f.read())
                    if nb["metadata"]["kernelspec"]["language"] in languages:
                        for cell in nb["cells"]:
                            if cell["metadata"]["kernel"] == "SysML" and cell["cell_type"] == "code":
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

                                # Make model data object
                                model_id = cell["id"]
                                model_hash = str(hash(model_text))
                                path_text = os.path.join(dir_path, name)
                                path_hash = str(hash(path_text))
                                models[model_id] = [model_num, model_text, model_hash, path_text, path_hash, '', '']
                                model_num += 1
                                #print('-------------\n',model_text)

                            ## End found a cell that's SysML
                        ## End for cell in cells
                    ## End check if notebook has any SysML
                ## End open file

                if len(models) > 0:
                    # Put all the SysML in a new notebook
                    new_nb = _base_nb()
                    cells = []
                    for model_id in models:
                        model_text = models[model_id][1]
                        cells.append(_make_nb_cell(model_id, model_text))
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
                            if cell["metadata"]["kernel"] == "SysML" and cell["cell_type"] == "code":
                                # Find the output which must exist now
                                for out in cell["outputs"]:
                                    # Find the right output to continue
                                    if "data" in out.keys():
                                        if "text/plain" in out["data"]:
                                            id_cell = cell["id"]
                                            names = out["data"]["text/plain"]
                                            for nam in names:
                                                obj_name = " ".join(
                                                    nam.split(" (")[0]
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
                        if " " in obj_name[1]:
                            tname = '"'+obj_name[1]+'"'
                        else:
                            tname = obj_name[1]

                        cells.append(
                            _make_nb_cell(
                                str(uuid_lib.uuid4()),
                                "%export "+tname,
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
                            if cell["metadata"]["kernel"] == "SysML" and cell["cell_type"] == "code":
                                # Find the output which must exist now
                                for out in cell["outputs"]:
                                    # Find the right output to continue
                                    if "data" in out.keys():
                                        if "text/html" in out["data"]:
                                            html = out["data"]["text/html"][0]
                                            data = json.loads(base64.b64decode(html[html.find('href=')+35:-14]))
                                            #print(json.dumps(data, sort_keys=True, indent=10))
                                            element_name = cell["source"][0][8:]
                                            id_cell = cell["metadata"]["tags"][0]
                                            models[id_cell][-2] = element_name
                                            models[id_cell][-1] = json.dumps(data)
                                            ## End if valid name, otherwise can't export
                                        ## End for name
                                    ## End check correct data output
                                ## End for each cell output
                            ## End this cell is SysML
                        ## End for each cell
                    ## Close file
                all_models[name] = models.copy()
            ## End check if correct file type
        ## End for file in files

    # models[notebook_path][nb_id] =
    #   [model_execution_number, model_text, model_hash, path_text, path_hash, name, elementAPIJSON]


    valid_models = {} # Remove any model that could not be parsed
    all_elements = {} # A dictionary of all elements to be created

    for notebook in all_models:
        q = PriorityQueue()
        for nb_id in all_models[notebook]:
            q.put((all_models[notebook][nb_id][0], nb_id))

        while not q.empty():
            nb_id = q.get()[1]

            if all_models[notebook][nb_id][-1] != '':
                elements = json.loads(all_models[notebook][nb_id][-1])
                new_elements = []
                old_elements = []
                # Create a temp folder
                if DEBUG:
                    path = 'tmp/'+all_models[notebook][nb_id][3] \
                        .replace('"','') \
                        .replace(" ","_")
                    if not os.path.exists(path):
                       # Create a new directory because it does not exist
                       os.makedirs(path)
                       print("The new directory is created!")

                for element in elements:
                    if not element['identity']['@id'] in all_elements:
                        # Add this element
                        all_elements[element['identity']['@id']] = element
                        new_elements.append(element['identity']['@id'])
                    else:
                        # This element existed already
                        old_elements.append(element['identity']['@id'])

                    if DEBUG:
                        path2 = element['payload']['@type']+element['identity']['@id']+'.json'
                        with open(os.path.join(path, path2),'w') as f:
                            json.dump(element,f,indent=3)

                all_models[notebook][nb_id][-1] = new_elements+old_elements
                all_models[notebook][nb_id].append(new_elements)

                # Put this in a valid dictionary
                if not notebook in valid_models:
                    valid_models[notebook] = {}
                valid_models[notebook][nb_id] = all_models[notebook][nb_id].copy()
            else:
                # This model could not be made into JSON, it might be invalid.
                pass
    return valid_models, all_elements

def collect_tool_execution_metadata(elements, a, actions):
    """Collect tool execution metadata (tool name and URI) for an action.

    The SysML export describes tool metadata via `MetadataUsage` and
    `ReferenceUsage` sub-elements. This function finds those definitions and
    extracts the declared `toolName` and `uri`, then stores them into the
    `actions` structure under `tools.harbor` or `tools.artifacts` depending
    on the configured tool names in `env.py`.
    """
    # If there are no owned Elements there is nothing to do
    if a.get_key('ownedElement') is None:
        return []

    # Get all owned elements of MetadataUsage with correct definition
    tools = [x for x in a.find_subelements(
            'ownedElement',
            'MetadataUsage',
            elements
        ) if x.get_subelement(
            'metadataDefinition',
            elements) \
        .get_key('qualifiedName') == \
            "AnalysisTooling::ToolExecution"
    ]

    # Now get names and uris
    for t in tools:
        # Set default name and uri
        toolName = None
        uri = None

        # This gets the redefined values
        # e.g. [["toolName", "Artifacts"], ["uri", "git://example.com"]]
        tool_variables = [
            [x.get_subelement(
                'ownedRedefinition',
                elements
            ).get_subelement(
                'redefinedFeature',
                elements
            ).get_key('qualifiedName'),
            x.get_subelement(
                'ownedRedefinition',
                elements) \
            .get_subelement(
                'redefiningFeature',
                elements) \
            .get_subelement(
                'ownedElement',
                elements) \
            .get_key('value')
            ] \
            for x in t.find_subelements(
                'ownedElement',
                'ReferenceUsage',
                elements
            )
        ]

        # Now we pull out the values to overwrite
        toolName = [x[1] for x in tool_variables if 'toolName' in x[0]][0]
        uri = [x[1] for x in tool_variables if 'uri' in x[0]][0]

        if toolName == HARBORTOOL:
            actions[a.get_id()]['tools']['harbor'] = {
                'toolName' : toolName,
                'uri' : uri
            }
            print('      Action has a harbor definition: {}'.format(uri))
        elif toolName == ARTIFACTSTOOL:
            actions[a.get_id()]['tools']['artifacts'] = {
                'toolName' : toolName,
                'uri' : uri
            }
            print('      Action has an artifact definition: {}'.format(uri))
        else:
            # Skip a tool that doesn't match these
            continue

    return actions

def find_variable_name(elements, i):
    """Extract the declared tool variable name from an input element.

    The SysML export encodes tool variable names as a `MetadataUsage` whose
    owned elements include a `name` entry. Return the string value or `None`
    if not found.
    """
    tvn = None
    for ioe in i.get_subelements('ownedElement', elements).get_elements():
        # Ensure this is a metadata usage
        if ioe.get_type() != 'MetadataUsage':
            print('         Skipping element {}.'.format(ioe.get_type()))
            continue

        # Ensure this is the right type of metadata
        if ioe.get_subelement('metadataDefinition', elements) \
            .get_key('qualifiedName') != "AnalysisTooling::ToolVariable":
            print('         Skipping metadata not associated with ToolVariable.')
            continue

        key = None
        ioeoe = ioe.get_subelements('ownedElement', elements)
        # Go through all the metadata elements looking for name
        for k,v in enumerate(ioeoe.get_elements()):

            # Ensure that the metadata has an element named name
            if v.get_key('name') != 'name':
                print('         Skipping owned metadata with name {}.'.format(v.get_key('name')))
                continue

            # We've found the metadata, stop searching for the key
            key = k
            break

        # Grab the tool metadata from our search
        tv = ioeoe.get_elements()[key]

        # Get the owned elements from this name metadata.
        tn = tv.get_subelement('ownedElement', elements)

        # Set the name equal to the value
        tvn = tn.get_key('value')
        print('         Found variable named: {}'.format(tvn))

        break

    return tvn

def find_variable_value(elements, i, tn):
    """Given an input element `i`, locate the value for tool variable `tn`.

    This inspects owned elements of the input to determine whether the value
    is a literal, a feature chain (reference to an output), or something
    else. Returns a dict mapping `tn` to the discovered value (or an empty
    string when a value couldn't be found).
    """
    # elements -- All elements
    # i -- This input element
    # tn -- The tool variable name
    for ioe in i.get_subelements('ownedElement', elements).get_elements():
        if ioe.get_type() == 'MetadataUsage':
            # Skip metadata usage wrappers — these don't contain the value
            continue

        ename = ioe.get_key("declaredName")

        if ename is None:
            ename = ioe.get_type()

        print("      Element: {}".format(ename))

        # If the element is a literal, extract it directly
        literal, v = handle_literals(ioe)
        if literal:
            # Just go to the next element, it's been handled.
            return {tn: v}

        # If the value is produced by a feature chain (e.g. referencing an
        # action output), delegate to the feature-chain handler
        if ioe.get_type() == "FeatureChainExpression":
            return handle_feature_chain(elements, ioe, tn)
        else:
            # No chaining feature and not a literal — return an empty value
            print("         Skipping over element: {}".format(ioe.get_type()))
            return {tn: ''}

def handle_action_inputs(elements, i, a, actions):
    """Extract tool variable values for a given input and attach them to
    the `actions` dict under `tools.variables`.

    Steps:
      - locate the tool variable name (metadata)
      - locate the tool variable value (literal, feature chain, etc.)
      - attach the discovered value and chosen units to `actions`
    """
    print('      Checking for tool variable name metadata')

    # Check that something returns for the element
    if i.get_key('ownedElement') is None:
        print('      Input had no metadata, skipping.')
        return actions

    # Find the tool variable name
    tn = find_variable_name(elements, i)

    # The variable name could not be found.
    if tn is None:
        return actions

    # Variable name has been found, now find the data
    print('      Found tool metadata.')

    # Find the tool variable value
    tv = find_variable_value(elements, i, tn)

    if not 'variables' in actions[a.get_id()]['tools']:
        actions[a.get_id()]['tools']['variables'] = {}

    for name in list(tv.keys()):
        # Attach with default units; callers may interpret units specially
        actions[a.get_id()]['tools']['variables'][name] = {
            'value': tv[name],
            'units': "u.one"
        }

    return actions


def updated_model_parse_actions(elements, a, prev_a, actions, v, verifications):
    """Process a discovered action usage and collect stored data and tooling.

    This updates the `actions` structure with any stored data (via
    `add_stored_data`), collects configured tooling metadata (container and
    artifacts URIs) and, when both tooling entries exist, extracts any
    declared variables from the action inputs.
    """
    print('   Found an action -- {}'.format(a.get_id()))
    actions, prev_a, verifications = add_stored_data(
        a, prev_a, actions, v, verifications
    )
    print('   Searching if this action has metadata associated with tooling.')
    actions = collect_tool_execution_metadata(elements, a, actions)

    # If required tool metadata is missing, bail out early
    if actions[a.get_id()]['tools']['harbor'] is None or \
        actions[a.get_id()]['tools']['artifacts'] is None:
        return actions, prev_a, verifications

    print('   Action has required tool metadata, grabbing variables.')

    # Make a new element list with all inputs and extract variable values
    inputs = Elements(a.get_key('input'), elements)

    for i in inputs.get_elements():
        # Check if this input has a tool name, otherwise drop
        actions = handle_action_inputs(elements, i, a, actions)

    print('   Action variables: {}'.format(actions[a.get_id()]['tools']['variables']))

    return actions, prev_a, verifications

## DEPRECATED
def alpha_model_parse_actions(elements, a, prev_a, actions, v, verifications):
    """Deprecated parsing path retained for historical reasons.

    This function contains an older approach to extracting tool metadata
    and variables from action usages. New code should use
    `updated_model_parse_actions` instead.
    """
    print('   Found an action -- {}'.format(a.get_id()))
    actions, prev_a, verifications = add_stored_data(
        a, prev_a, actions, v, verifications
    )
    print('   Searching if this action has metadata associated with tooling.')

    tools = [x for x in a.find_subelements(
            'ownedMember',
            'MetadataUsage',
            elements
        ) if x.get_subelement(
            'metadataDefinition',
            elements) \
        .get_key('qualifiedName') == \
            "AnalysisTooling::ToolExecution"
    ]
    #print(tools)

    for t in tools:
        toolName = None
        uri = None

        tool_variables = [
            [x.get_subelement(
                'ownedRedefinition',
                elements
            ).get_subelement(
                'redefinedFeature',
                elements
            ).get_key('qualifiedName'),
            x.get_subelement(
                'ownedRedefinition',
                elements) \
            .get_subelement(
                'redefiningFeature',
                elements) \
            .get_subelement(
                'ownedElement',
                elements) \
            .get_key('value')
            ] \
            for x in t.find_subelements(
                'ownedMember',
                'ReferenceUsage',
                elements
            ) if ( "AnalysisTooling::ToolExecution" in \
                x.get_subelement(
                    'ownedRedefinition',
                    elements
                ).get_subelement(
                    'redefinedFeature',
                    elements) \
                .get_key('qualifiedName')
            )
        ]
        #print(tool_variables)

        toolName = [x[1] for x in tool_variables if 'toolName' in x[0]][0]
        uri = [x[1] for x in tool_variables if 'uri' in x[0]][0]

        if toolName == HARBORTOOL:
            actions[a.get_id()]['tools']['harbor'] = {
                'toolName' : toolName,
                'uri' : uri
            }
            print('      Action has a harbor definition: {}'.format(uri))
        elif toolName == ARTIFACTSTOOL:
            actions[a.get_id()]['tools']['artifacts'] = {
                'toolName' : toolName,
                'uri' : uri
            }
            print('      Action has an artifact definition: {}'.format(uri))
        else:
            pass

    if actions[a.get_id()]['tools']['harbor'] is not None and \
        actions[a.get_id()]['tools']['artifacts'] is not None:
        print('   Action has required tool metadata, grabbing variables.')
        inputs = Elements(a.get_key('input'), elements)
        for i in inputs.get_elements():
            # Check if this input has a tool name, otherwise drop
            print('      Checking for tool variable name metadata')
            tool_variables = [
                x.get_subelement(
                    'featureMembership',
                    elements
                ).get_subelement(
                    'target',
                    elements
                ).get_subelement(
                    'ownedElement',
                    elements
                ).get_key('value') for x in i.find_subelements(
                    'ownedElement',
                    'MetadataUsage',
                    elements
                ) if x.get_subelement(
                    'metadataDefinition',
                    elements) \
                .get_key('qualifiedName') == \
                    "AnalysisTooling::ToolVariable" and \
                x.get_subelement(
                    'featureMembership',
                    elements
                ).get_subelement(
                    'target',
                    elements
                ).get_subelement(
                    'ownedElement',
                    elements
                ).istype('LiteralString')
            ]

            if len(tool_variables) == 0:
                print('      This input was missing metadata')
                continue

            # Skip this for now
            # list_variable = [
                # [
                    # y.dump(elements) for y in x.get_subelements(
                        # 'argument',
                        # elements
                        # ).get_elements()
                # ] for x in i.find_subelements(
                    # 'ownedElement',
                    # 'OperatorExpression',
                    # elements
                # )

            # Look to see if this is a feature chain to a feature,
            # This would point to an output
            print('      Found tool metadata.')
            reg_variable = [
                x.get_subelement(
                    'targetFeature',
                    elements
                ).get_subelement(
                    'chainingFeature',
                    elements,
                    index = -1 # Grab the last element in this chain
                ) for x in i.find_subelements(
                    'ownedElement',
                    'FeatureChainExpression',
                    elements
                ) if x.get_subelement(
                    'targetFeature',
                    elements
                ).istype('Feature')
            ]

            if len(reg_variable) == 1:
                # Try to pull the information out

                val_variable = [
                    x.get_subelement(
                        'value',
                        elements
                    ) for x in reg_variable[0].find_subelements(
                        'ownedElement',
                        'LiteralInteger',
                        elements
                    )
                ]

                if len(val_variable) == 0:
                    # This might be a string
                    val_variable = [
                        x.get_subelement(
                            'value',
                            elements
                        ) for x in reg_variable[0].find_subelements(
                            'ownedElement',
                            'LiteralString',
                            elements
                        )
                    ]

                    if len(val_variable) == 0:
                        # Check if this is a unit
                        val_variable = [
                            x.get_subelements(
                                'argument',
                                elements
                            ) for x in reg_variable[0].find_subelements(
                                'ownedElement',
                                'OperatorExpression',
                                elements
                            )
                        ]

                        if len(val_variable) == 1:
                            val = None
                            for u in val_variable[0].get_elements():
                                if u.istype('LiteralInteger'):
                                    val = u.get_key('value')
                                elif u.istype('FeatureReferenceExpression'):
                                    units = u.get_subelement(
                                        'referent',
                                        elements
                                    ).get_key('shortName')
                            if val is None:
                                # Couldn't find an integer
                                raise NotImplementedError
                            val_variable = val
                        else:
                            raise

                    else:
                        val_variable = val_variable[0]
                        units = 'string'
                else:
                    val_variable = val_variable[0]
                    units = 'u.one'

            else:
                # Try for reference usage to an action output
                reg_variable = [
                    x.get_subelement(
                        'targetFeature',
                        elements
                    ).get_subelement(
                        'owningUsage',
                        elements
                    ) for x in i.find_subelements(
                        'ownedElement',
                        'FeatureChainExpression',
                        elements
                    ) if x.get_subelement(
                        'targetFeature',
                        elements
                    ).get_subelement(
                        'owningUsage',
                        elements
                    ).istype('ActionUsage')
                ]

                if len(reg_variable) == 0:
                    continue

                val_variable = reg_variable[0].get_key('qualifiedName')
                units = 'minio'

            if not 'variables' in actions[a.get_id()]['tools']:
                actions[a.get_id()]['tools']['variables'] = {}

            for tv in tool_variables:
                actions[a.get_id()]['tools']['variables'][tv] = {
                    'value': val_variable,
                    'units': units
                }
    return actions, verifications

def handle_verification(element_id, e, elements, actions, verifications):
    """Register a verification and parse its child actions.

    Creates an entry in `verifications` with basic metadata and then finds
    associated `ActionUsage` sub-elements (via feature memberships). Each
    discovered action is processed with the updated parsing routine which
    collects tool metadata and variables.
    """
    # Create a verification
    print('Found a verification -- {}'.format(element_id))
    v = e
    verifications[v.get_id()] = {
        'shortName': v.get_key('shortName'),
        'declaredName': v.get_key('declaredName'),
        'qualifiedName': v.get_key('qualifiedName'),
        'requirements': v.get_key('verifiedRequirement'),
        'actions': []
    }

    # Find action usages that are members of this verification
    print('Searching for actions.')
    subactions = [
        x.get_subelement(
            'memberElement',
            elements) \
        for x in v.find_subelements(
            'ownedFeatureMembership',
            'FeatureMembership',
            elements
        ) if x.get_subelement(
            'memberElement',
            elements) \
        .istype('ActionUsage')
    ]

    # TODO: Handle single container version that isn't listed in an action

    prev_a = None
    for a in subactions:
        # DEPRECATED -- Old parse function
        #actions, prev_a, verifications = alpha_model_parse_actions(
        #    elements, a, prev_a, actions, v, verifications
        #)
        # New function to match sysml-windstorm
        actions, prev_a, verifications = updated_model_parse_actions(
            elements, a, prev_a, actions, v, verifications
        )

    return actions, verifications

def handle_requirement(e, requirements):
    """Register a requirement usage when it represents a real requirement.

    The function filters out internal/object names that include `::obj` and
    ensures the qualified name looks like a hierarchical SysML qualified
    name (contains `::`). If valid, the requirement's short/declared/qualified
    names are stored in the `requirements` mapping.
    """
    if not '::' in e.get_key('qualifiedName'):
        return requirements

    if 'obj' in e.get_key('qualifiedName').split('::'):
        return requirements

    requirements[e.get_id()] = {
        'shortName': e.get_key('shortName'),
        'declaredName': e.get_key('declaredName'),
        'qualifiedName': e.get_key('qualifiedName'),
    }

    return requirements

def parse_models(models, elements):
    """Top-level parser: convert exported elements into requirements,
    verifications and actions structures.

    Iterates over each exported element, classifies it (verification or
    requirement) and dispatches to the appropriate handler. Returns three
    dictionaries: `requirements`, `verifications`, and `actions` that are
    suitable for insertion into the database layer.
    """
    verifications = {}
    requirements = {}
    actions = {}

    # Go through each element and classify
    for element_id in elements:
        # Make the element a class so we have functions
        e = Element(element_id, elements)

        # If this is a verification, parse its actions and metadata
        if e.istype('VerificationCaseDefinition'):
            actions, verifications = handle_verification(
                element_id, e, elements, actions, verifications
            )

        # If this is a requirement usage, record it
        elif e.istype('RequirementUsage') and \
            e.get_key('qualifiedName')[-5:] != '::obj':
            requirements = handle_requirement(e, requirements)

    # Print a summary to aid debugging (keeps original behavior)
    print('\n\n\n\n---------------------')
    print('Listing all verifications found.')
    for element_id in verifications:
        print('Verification: {}'.format(verifications[element_id]['declaredName']))
        for reqt in verifications[element_id]['requirements']:
            print('   validates Requirement {}'.format(requirements[reqt['@id']]['declaredName']))
        for action in verifications[element_id]['actions']:
            print('   has action: {}'.format(action['declaredName']))
            valid = True
            if actions[action['id']]['tools']['harbor'] is not None:
                print ('      has container image: {}'.format(actions[action['id']]['tools']['harbor']['uri']))
            else:
                valid = False
            if actions[action['id']]['tools']['artifacts'] is not None:
                print ('      has artifacts at: {}'.format(actions[action['id']]['tools']['artifacts']['uri']))
                if 'variables' in actions[action['id']]['tools']['artifacts']:
                    for v in actions[action['id']]['tools']['artifacts']['variables']:
                        if actions[action['id']]['tools']['artifacts']['variables'][v]['units'] == 'minio':
                            print('      will direct file(s) {} from action: {}'.format(v,actions[action['id']]['tools']['artifacts']['variables'][v]['value']))
                        elif actions[action['id']]['tools']['artifacts']['variables'][v]['units'] == 'string' or \
                            actions[action['id']]['tools']['artifacts']['variables'][v]['units'] == 'u.one':
                            print('      has variable {} = {}'.format(v,actions[action['id']]['tools']['artifacts']['variables'][v]['value']))
                        else:
                            print('      has variable {} = {} [{}]'.format(v,actions[action['id']]['tools']['artifacts']['variables'][v]['value'],actions[action['id']]['tools']['artifacts']['variables'][v]['units']))
            else:
                valid = False
            if valid:
                print('      is a valid DigitalForge validation.')
            else:
                print('      is not a valid DigitalForge validation.')

    print('\n\n\n\n---------------------')
    print('Listing all requirements found.')
    for element_id in requirements:
        print('Requirement: {}'.format(requirements[element_id]['declaredName']))

    return requirements, verifications, actions
