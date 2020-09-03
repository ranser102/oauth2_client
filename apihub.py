import archive
import jwt
import os
import secrets
from datetime import datetime, timedelta
from flask import Flask,request, jsonify, redirect, session, url_for
from requests_oauthlib import OAuth2Session

from __main__ import app
from adminapi import checkJWT



##########################
@app.route('/api/v1/archive',methods=['GET','PATCH']) 
def archiveProject():
    isError = False
    returnCode ='200'
    response = 'success'
    jwtoken = None

    runMode = 'c'
    if 'token' in request.args:
        runMode = 'r'
        jwtoken = request.args['token']
        authorized = checkJWT(jwtoken)
    if not jwtoken or not authorized:
        isError = True
        returnCode = '401'
        response = 'Unauthorized to archive'
        return jsonify(isError= isError, statusCode= returnCode,data= response), returnCode

    projectName = ''
    if 'project' in request.args:
        projectName = request.args['project']
    if projectName == '':
        response = 'Error: project is missing'
        returnCode = '404'
        isError = True
    else:
        argv=['-p',projectName,'-m',runMode]
        try:
            response, isError = archive.archive_main(argv)
            returnCode = '401' if '401' in response else '200'
            print("archiveProject")
        except:
            response = "Error processing request. Note: GITLAB_TOKEN should be exported as an environment variable"
            returnCode = '404'
            isError = True
        finally:
            return jsonify(isError= isError,
                        statusCode= returnCode,
                        data= response), returnCode

    return jsonify(isError= isError, statusCode= returnCode,data= response), returnCode

##########################