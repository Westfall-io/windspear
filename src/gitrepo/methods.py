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

import time
import copy

import git

# gitrepo/methods.py: helpers to clone and checkout git repositories for
# processing. Functions here wrap `GitPython` calls to obtain repository
# contents and commit metadata needed by the rest of the pipeline.

def checkout_branch_commit(ref, commit, repopath):
    # Clone the repository URL (optionally injecting credentials), checkout
    # the requested branch, collect commit metadata, then check out the
    # specific commit for analysis.
    print(repopath, GITHOST)
    if GITUSER == '':
        repopath = GITHOST + repopath
    else:
        h = copy.deepcopy(GITHOST)
        parts = h.split('//')
        parts.insert(1,'{}:{}@'.format(GITUSER, GITPASS))
        parts.insert(1,'//')
        repopath = ''.join(parts) + repopath
    print(repopath)
    # Clone the repo into the current working directory
    git.Git(".").clone(repopath)
    # Normalize the repo path to extract domain/owner/repo for locating
    # the cloned directory on disk.
    httppath = repopath[repopath.find('/')+2:]
    httpparts = httppath.split("/")
    domain = httpparts[0]
    repoowner = httpparts[1]
    dir_path = httpparts[2]
    repo = git.Repo(dir_path)
    branch = ref.split('/')[-1]
    repo.git.switch(branch)
    commit_data = get_commit_data(repo)
    repo.git.checkout(commit)
    return dir_path, branch, commit_data

def get_commit_data(repo):
    # Return a list of recent commits with ISO8601 timestamps and hex SHA.
    format = '%Y-%m-%dT%H:%M:%S%z'
    commits = repo.iter_commits(max_count=100)
    commit_data = []
    for commit in commits:
        commit_data.append([time.strftime(format, time.localtime(commit.committed_date)),commit.hexsha])

    return commit_data
