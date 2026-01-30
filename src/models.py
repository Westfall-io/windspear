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
# models.py: Lightweight in-memory representations for parsed SysML artifacts.
#
# This module defines simple container classes used by the pipeline to hold
# verifications, actions, and tool execution metadata extracted from models.
# These objects are intentionally minimal and provide `load`/`dump` helpers
# to convert between Python-native structures and JSON-friendly forms.
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
        # Populate this Verifications container from a dictionary mapping
        # ids to raw verification data (typically decoded from parsed model
        # output). Each entry is converted to a `Verification` instance.
        # The `json` flag is reserved for future JSON-specific handling.
        for vid in verifications:
            self.verifications[vid] = Verification.load(verifications[vid])
        return self
#
    def dump(self):
        # Return a JSON string representing all stored verifications. Each
        # verification is converted to a serializable dict via `dump()`.
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
        # Add an `Action` to this verification. Parameters are the action id,
        # declared name, and qualified name from the parsed model.
        self.actions.append(Action(id, declaredName, qualifiedName))
        return self
#
    def load(verification, json=False):
        # Load data from a mapping (e.g., from parsed JSON) onto this
        # Verification instance. This expects keys like 'id', 'declaredName',
        # 'qualifiedName' and an iterable under 'actions'.
        self.id = verification['id']
        self.declaredName = verification['declaredName']
        self.qualifiedName = verification['qualifiedName']
        for a in verification['actions']:
            self.add_actions(Action.load(a))
#
    def dump(self):
        # Serialize this verification to a JSON-compatible structure. The
        # method returns True after writing to JSON for compatibility with
        # the original code's expectations.
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
        # Return a JSON string describing the tool execution. The resulting
        # structure is intentionally simple and may be adjusted to match
        # downstream consumers' expectations.
        return json.dumps({'name': 'Harbor', 'uri': self.uri})
#
if __name__ == '__main__':
    th = ToolExecution('Harbor', 'uri://uri')
    ta = ToolExecution('Artifacts', 'uri://uri')

    v = Verification(1, 'req', 'reqs::req')
