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
#
class Verifications:
    def __init__(self):
        self.verifications = {}
#
    def add_verification(self, id, verification):
        self.verifications[id] = verification
        return self
#
    def load(self, verifications, json=False):
        # From dictionary
        for vid in verifications:
            self.verifications[vid] = Verification.load(verifications[vid])
        return self
#
    def dump(self):
        return json.dumps([self.verifications[vid].dump() for vid in self.verifications])
#
#
class Verification:
    def __init__(self, id, qualifiedName, verifiedRequirement):
        self.id = id
        self.name = qualifiedName
        self.requirements = verifiedRequirement
        self.actions = []
#
    def add_actions(id, declaredName, qualifiedName):
        self.actions.append(Action(id, declaredName, qualifiedName))
        return self
#
    def load(verification, json=False):
        self.id = verification['id']
        self.declaredName = verification['declaredName']
        self.qualifiedName = verification['qualifiedName']
        for a in verification['actions']:
            self.add_actions(Action.load(a))
#
    def dump(self):
        json.dump({
            'id': self.id,
            'declaredName': self.declaredName,
            'qualifiedName': self.qualifiedName,
            'actions': self.actions.dump()})
        return True
#
class Action:
    def __init__(self, id, declaredName, qualifiedName):
        self.id = id
        self.declaredName = declaredName
        self.qualifiedName = qualifiedName
        self.tools = {
            'harbor': None,
            'artifacts': None,
            'variables': [],
        }
#
    def add_tool(self, te):
        if te.toolName.lower() == 'harbor':
            self.tools['harbor'] = te
        elif te.toolName.lower() == 'artifacts':
            self.tools['artifacts'] = te
#
class ToolExecution:
    def __init__(self, toolName, uri):
        self.toolName = toolName
        self.uri = uri
#
    def load(self, tool):
        self.toolName = tool['toolName']
        self.uri = tool['uri']
#
    def dump(self):
        return json.dumps({'name': 'Harbor', 'uri': self.uri})
#
if __name__ == '__main__':
    th = ToolExecution('Harbor', 'uri://uri')
    ta = ToolExecution('Artifacts', 'uri://uri')

    v = Verification(1, 'req', 'reqs::req')
