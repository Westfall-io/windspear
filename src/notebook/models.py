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

import json

def _print_element(element, elements, missing=False):
    new_element = {}
    element = element['payload']
    for key in element:
        if '@id' in json.dumps(element[key]):
            if isinstance(element[key], list):
                new_element[key] = []
                for v in element[key]:
                    if v['@id'] in elements:
                        new_element[key].append({
                            '@id': v['@id'],
                            '@type': elements[v['@id']]['payload']['@type']
                        })
                        for key2 in elements[v['@id']]['payload']:
                            if 'name' in key2:
                                new_element[key][-1][key2] = elements[v['@id']]['payload'][key2]
                    else:
                        if missing:
                            new_element[key].append({
                                '@id': v['@id'],
                                '@type': '404 Not Found'
                            })
            elif isinstance(element[key], dict):
                if element[key]['@id'] in elements:
                    new_element[key] = {
                        '@id': element[key]['@id'],
                        '@type': elements[element[key]['@id']]['payload']['@type']
                    }

                    for key2 in elements[element[key]['@id']]['payload']:
                        if 'name' in key2:
                            new_element[key][key2] = elements[element[key]['@id']]['payload'][key2]
                else:
                    if missing:
                        new_element[key] = {
                            '@id': element[key]['@id'],
                            '@type': '404 Not Found'
                        }
        else:
            new_element[key] = element[key]
    print(json.dumps(new_element, indent=3))

class Element:
    def __init__(self, id, elements):
        self.id = id
        self.element = elements[id]

    def dump(self, elements):
        return _print_element(self.element, elements)

    def get_key(self, key, default=None):
        if key in self.element['payload']:
            return self.element['payload'][key]
        else:
            return default

    def get_id(self):
        return self.id

    def istype(self, type):
        return self.element['payload']['@type'] == type

    def get_type(self):
        return self.element['payload']['@type']

    def find_subelements(self, key, type, elements):
        subelements = []
        val = self.get_key(key)
        if isinstance(val, list):
            for val_elements in val:
                if val_elements['@id'] in elements:
                    subelement = elements[val_elements['@id']]
                    if subelement['payload']['@type'] == type:
                        subelements.append(Element(val_elements['@id'], elements))
        elif isinstance(val, dict):
            subelement = elements[val['@id']]
            if subelement['payload']['@type'] == type:
                subelements.append(Element(val['@id'], elements))
        else:
            raise NotImplementedError('Not sure how to handle this.')
        return subelements

    def get_subelement(self, key, elements, index=0):
        val = self.get_key(key)
        if isinstance(val, dict):
            subelement = Element(val['@id'], elements)
        elif isinstance(val, list):
            # Always return the first element
            subelement = Element(val[index]['@id'], elements)
            if len(val) > 1:
                print('Warning: More than one value was found in this reference.')
                print('The list returned was: {}'.format(val))
        elif isinstance(val, str) or isinstance(val, int) or isinstance(val, float):
            subelement = val
        else:
            print('Error when attempting to find key: {} with type: {}'.format(key,type(val)))
            raise NotImplementedError('Not sure how to handle this.')
        return subelement

    def get_subelements(self, key, elements):
        val = self.get_key(key)
        if isinstance(val, list):
            if len(val) == 0:
                # If an empty list is returned, return an empty list
                return []
            # Return all elements
            return Elements(val, elements)
        else:
            # Return one value
            return self.get_subelement(self, key, elements)

    def get_elements(self):
        # This function will mimic Elements by returning the element
        # inside a list
        return [self]

class Elements:
    def __init__(self, ids, elements):
        self.elements = [Element(x['@id'], elements) for x in ids]

    def get_elements(self):
        return self.elements
