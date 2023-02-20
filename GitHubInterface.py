# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 17:34:15 2023

@author: Feli
"""

import base64
import requests
from github import Github
from github import InputGitTreeElement        

"""Upload the database to Github"""
def uploadDatabase(access, files_to_upload, commit_message):
    g = Github(access)
    repo = g.get_user().get_repo('ELO')

    master_ref = repo.get_git_ref('heads/databaseUpdates')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = list()
    for i, entry in enumerate(files_to_upload):
        if entry.endswith('.fs'):
            with open(entry,mode='rb') as input_file:
                data = input_file.read()
                data = base64.b64encode(data)
                blob = repo.create_git_blob(data.decode("utf-8"), "base64")
                element = InputGitTreeElement(entry, '100644', type='blob', sha=blob.sha)
        else:
            with open(entry) as input_file:
                data = input_file.read()
                element = InputGitTreeElement(entry, '100644', 'blob', data)
#    element = InputGitTreeElement(filestorage_name, '100644', type='blob', sha=blob.sha)
    element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)
    
"""Fetch the database filesystem from Github to working directory"""
def downloadDatabase(filestorage_name):
    url = 'https://raw.githubusercontent.com/FeMaWi/ELO/databaseUpdates/' + filestorage_name
    req = requests.get(url)
    f = open('TheRealShit.fs', 'w+b')
    f.write(req.content)
    f.close()
    return