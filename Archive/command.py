#!/bin/python3
"""
Provides command-line interface for archiving project.
@author: Eran Sery
"""

########################################################################
# Imported modules
########################################################################

import os
import sys
import logging
import requests
import getopt
import json

apiUrl = 'https://example.gitlab.com/api/v4/'

########################
def _exit_program_(exit_code):
	print(sys.argv[0] + '\n\t -p|--project <project name> \n' +
                        '\t -m|--mode <Run mode. Valid Values "c/check" or "r/run"> \n' +
                        '\t -h/--help \n' +
                        '\t Note: GITLAB_TOKEN should be exported as an environment variable')
	sys.exit(exit_code)

########################
def _get_input(argv):
    projectName = ''
    mode = ''
    token = ''

    try:
        opts, args = getopt.getopt(argv,"hp:m:",["project","mode","help"])
        token = os.getenv('GITLAB_TOKEN')
    except getopt.GetoptError:
        _exit_program_(1)
    for opt, arg in opts:
        if opt == ("-h","--help"):
            _exit_program_(0)
        elif opt in ("-p", "--project"):
            projectName = arg
        elif opt in ("-m", "--mode"):
            mode = arg                 

    if projectName == '' or not projectName  or mode == '' or not mode or token == '' or not token:
        _exit_program_(2)
    else:
        return projectName,mode,token



########################
def _retreive_projectid(project,token):
    global apiUrl 

    gitlabProjectName = ''
    gitlabProjectId = ''
    gitlabProjectArchived = ''
    
    apiType = 'projects'
    apiSearchParams = {'search_namespaces':'true','pagenation':'keyset','per_page': '50000','order_by': 'name','sort':'asc','search': project}
    apiHeaders = {'PRIVATE-TOKEN': token}
    try:
        resp = requests.get(apiUrl + apiType ,headers=apiHeaders,params=apiSearchParams)
        respJson = json.dumps(resp.json())
        respDict = json.loads(respJson)

        for projectDetails in respDict:
            if projectDetails['path_with_namespace'] == project:
                gitlabProjectName = projectDetails['path_with_namespace']
                gitlabProjectId = projectDetails['id']
                gitlabProjectArchived = projectDetails['archived']
                break
        return_status = 'success'
    except:
        print("Error searching for project: <" + project + ' >. Response: ' + resp.text)
        return_status = resp.text
    finally: 
        return gitlabProjectName,gitlabProjectId,gitlabProjectArchived,return_status

########################
def _archive_project(projID,name,mode,token):
    global apiUrl 
    apiType = 'projects'
    apiHeaders = {'PRIVATE-TOKEN': token}
    action = 'archive'

    if mode == 'r' or mode == 'run':
        try:
            resp = requests.post(apiUrl +'/'+ apiType +'/'+ str(projID) +'/'+ action ,headers=apiHeaders)
            return_status = 'finish archiving: ' + name 
            #print(resp.text)
        except:
            return_status = 'Error archiving  project: <' + name + ' >. Response: ' + resp.text
    else:
        return_status = 'Check mode: archiving <' + name + '>'
    
    return return_status

########################
def archive_main(argv):
    projectName, runMode, apiToken = _get_input(argv)
    projectID = 0
    isError = False

    fullProjectName, projectID, archiveStatus, return_sts  = _retreive_projectid(projectName,apiToken)
    if not archiveStatus:
        if fullProjectName == projectName:
            return_status = _archive_project(projectID,projectName,runMode,apiToken)
        else:
            if return_sts != 'success':
                return_status = return_sts
                isError = True 
            else:
                return_status  = 'Requested project: <' + projectName + '> not found. (Found: <' + fullProjectName + '>)'
                isError = True
    else:
        return_status = 'Found project: <' + fullProjectName + '>. Project already archived!'
    
    print(return_status)
    return return_status, isError

########################
if __name__ == "__main__": archive_main(sys.argv[1:])


