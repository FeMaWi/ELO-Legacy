# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 17:34:15 2023

@author: Feli
"""

import base64
from github import Github
from github import InputGitTreeElement        

def uploadDatabase(access, filestorage_name, commit_message):
    g = Github(access)
    repo = g.get_user().get_repo('ELO')

    master_ref = repo.get_git_ref('heads/databaseUpdates')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = list()
    with open(filestorage_name,mode='rb') as input_file:
        data = input_file.read()
        data = base64.b64encode(data)
        blob = repo.create_git_blob(data.decode("utf-8"), "base64")
    element = InputGitTreeElement(filestorage_name, '100644', type='blob', sha=blob.sha)
    element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)