import os
import time

import git

def checkout_branch_commit(ref, commit, repopath):
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
