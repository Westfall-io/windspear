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

DEBUG = os.environ.get("DEBUG",False)

SQLDEF = "localhost:5432"
SQLHOST = os.environ.get("SQLHOST",SQLDEF)

DBUSER = os.environ.get("DBUSER",'postgres')
DBPASS = os.environ.get("DBPASS",'mysecretpassword')
DBTABLE = os.environ.get("DBTABLE",'sysml2')

GITDEF = "https://models.westfall.io/"
GITHOST = os.environ.get("GITHOST",GITDEF)
GITUSER = os.environ.get("GITUSER",'')
GITPASS = os.environ.get("GITPASS",'')

APIDEF = "https://api.sysml.domain"
APIHOST = os.environ.get("APIHOST",APIDEF)

WINDSTORMHOST = os.environ.get(
    "WINDSTORMHOST",
    "http://windstorm-webhook-eventsource-svc.argo-events:12000/windstorm"
)

HARBORTOOL = os.environ.get("HARBORTOOL",'Harbor')
ARTIFACTSTOOL = os.environ.get("ARTIFACTSTOOL",'Artifacts')
