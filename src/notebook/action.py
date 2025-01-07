# Copyright (c) 2023-2025 Westfall Inc.
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

def add_stored_data(a, prev_a, actions, v, verifications):
    # Consider this a sim run
    verifications[v.get_id()]['actions'].append({
        'id' : a.get_id(),
        'declaredName' : a.get_key('declaredName'),
        'qualifiedName' : a.get_key('qualifiedName')
    })

    actions[a.get_id()] = {
        'verification': v.get_id(),
        'shortName': a.get_key('shortName'),
        'declaredName' : a.get_key('declaredName'),
        'qualifiedName' : a.get_key('qualifiedName'),
        'tools': {
            'harbor': None,
            'artifacts': None,
            'variables': {}
        }
    }

    # Add that this action is dependent on the previous
    if prev_a is not None:
        actions[a.get_id()]['dependency'] = prev_a
    prev_a = a.get_id()

    return actions, prev_a, verifications
