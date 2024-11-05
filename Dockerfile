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

FROM python:3.9-alpine3.18
#ENV REF=refs/heads/main
#ENV COMMIT=edf03b95f6f612de4bea9286418020f5beea74a6
#ENV GITHOST=https://git-http.gitea:3000/
ENV APIHOST="http://sysmlv2api.sysmlapi:9000"

### Install linux packages
RUN apk update && apk --no-cache add musl-dev \
  linux-headers \
  g++ \
  git \
  cmake \
  openblas-dev \
  gfortran \
  rust \
  cargo \
  python3-dev \
  libffi-dev \
  make \
  automake \
  gcc \
  libpq-dev \
  openjdk11

## Install python libraries
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

## Download and install SysML kernel
RUN wget https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/2023-07/jupyter-sysml-kernel-0.34.0.zip
RUN unzip jupyter-sysml-kernel-0.34.0.zip -d /tmp \
  && python3 /tmp/install.py

RUN sed 's|"env": {},|"env": {"ISYSML_API_BASE_PATH": "'$APIHOST'"},|' -i /usr/local/share/jupyter/kernels/sysml/kernel.json

WORKDIR /app
COPY src src

CMD ["python", "src/main.py", "", "", ""]
