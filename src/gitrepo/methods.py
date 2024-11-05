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

def checkout_branch_commit(ref, commit, repopath):
    print(repopath, GITHOST)
    if GITUSER == '':
        repopath = GITHOST + repopath
    else:
        h = copy.deepcopy(GITHOST)
        parts = h.split('//')
        parts.insert(1,'{}:{}'.format(GITUSER, GITPASS))
        parts.insert(1,'//')
        GITHOST = ''.join(x)
        repopath = GITHOST + repopath
    print(repopath)
    git.Git(".").clone(repopath)
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
    format = '%Y-%m-%dT%H:%M:%S%z'
    commits = repo.iter_commits(max_count=100)
    commit_data = []
    for commit in commits:
        commit_data.append([time.strftime(format, time.localtime(commit.committed_date)),commit.hexsha])

    return commit_data
