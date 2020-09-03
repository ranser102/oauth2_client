'''
export FLASK_APP=adminapi.py
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8
export GITLAB_TOKEN=<sometoken>
export JWT_SECRET=<somesecret>
For dev/test enable insecure server: export OAUTHLIB_INSECURE_TRANSPORT=1
    or: os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
export SECURED_HOSTING=True/False
'''

##########################

import jwt
import os,sys
import secrets
from datetime import datetime, timedelta
from flask import Flask,request, jsonify, redirect, session, url_for
from requests_oauthlib import OAuth2Session
import configparser
import requests
import json
import logging

app = Flask(__name__)
app.client_details={} 
import apihub

logging.basicConfig(level=logging.DEBUG)
os.getenv('SECURED_HOSTING')


##########################

def confDetails():
    '''
    Setup app.secret_key
    '''
    app.secret_key = secrets.token_urlsafe(16)

    '''
    Default values are in oauthclient.properties
    but environment variable will take precedence
    '''
    config = configparser.RawConfigParser()
    config.read('oauthclient.properties')
    app.client_details = dict(config.items('extendedapi'))
 
    app.client_details['secured_hosting'] = os.getenv('SECURED_HOSTING') if os.getenv('SECURED_HOSTING') else app.client_details['secured_hosting']
    app.client_details['oauthlib_insecure_transport'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT') if os.getenv('OAUTHLIB_INSECURE_TRANSPORT') else app.client_details['oauthlib_insecure_transport']
    app.client_details['client_id'] = os.getenv('CLIENT_ID') if os.getenv('CLIENT_ID') else app.client_details['client_id']
    app.client_details['client_secret'] = os.getenv('CLIENT_SECRET') if os.getenv('CLIENT_SECRET') else app.client_details['client_secret']
    app.client_details['authorization_base_url'] = os.getenv('AUTHORIZATION_BASE_URL') if os.getenv('AUTHORIZATION_BASE_URL') else app.client_details['authorization_base_url']
    app.client_details['token_url'] = os.getenv('TOKEN_URL') if os.getenv('TOKEN_URL') else app.client_details['token_url']
    app.client_details['callback_uri'] = os.getenv('CALLBACK_URI') if os.getenv('CALLBACK_URI') else app.client_details['callback_uri']
    app.client_details['api_url'] = os.getenv('API_URL') if os.getenv('API_URL') else app.client_details['api_url']


##########################
@app.route("/gitlabrequest")
def oauth():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. gitlab)
    using an URL with a few key OAuth parameters.
    For gitlab the redirect_uri value is mandatory and need to be match to the redirect_url
    in the gitlab client registration page
    """

    current_state = secrets.token_urlsafe(16)
    scheme = 'https://' if app.client_details['secured_hosting'] == 'True' else 'http://'
    session['redirect_uri'] = scheme + request.host + '/' + app.client_details['callback_uri']

    #### DEBUG
    app.logger.debug(session['redirect_uri'])
    #### DEBUG

    session['project']=request.args.get('project')
    session['request_type']=request.args.get('request_type')

    gitlab = OAuth2Session(app.client_details['client_id'],redirect_uri=session['redirect_uri'])
    authorization_url, state = gitlab.authorization_url(app.client_details['authorization_base_url'],state=current_state)

    # State is used to prevent CSRF
    if current_state == state:
        session['oauth_state'] = state
        return redirect(authorization_url)
    else:
        return jsonify(isError= true, statusCode= 500,data= 'Error returing from oauth server'), 500

##########################    

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    gitlab = OAuth2Session(app.client_details['client_id'], state=session['oauth_state'],redirect_uri=session['redirect_uri'])
    auth_code=request.args.get('code')

    try:
        token = gitlab.fetch_token(app.client_details['token_url'],client_secret=app.client_details['client_secret'],method=u'POST',code=auth_code)
    except:
        return redirect(url_for('.error'))

    # At this point you can fetch protected resources
    session['oauth_token'] = token

    errorMsg = ''
    wrongRequest = False
    if not session['project']:
        wrongRequest = True
        errorMsg +='<project> is missing! '
    if not session['request_type']:
        wrongRequest = True
        errorMsg +='<request_type> is missing! '
    if session['request_type'] != 'archive':
        wrongRequest = True
        errorMsg +='<request_type> ' + str(session['request_type']) + ' is not supported! '
    if not wrongRequest:
        if not _isUserMemeberOfProject():
            wrongRequest = True
            errorMsg +='Project <' + session['project'] + '> not found or user is not a memeber in the project! '
    
    scheme = 'https' if app.client_details['secured_hosting'] == 'True' else 'http'
    if wrongRequest:
        return redirect(url_for('.error',_scheme=scheme,_external=True,errormsg=errorMsg))
    
    return redirect(url_for('archiveProject',_scheme=scheme,_external=True,project=session['project'],token=_generateJWT()))
    
##########################
def _isUserMemeberOfProject():
    try:
        apiType='user'
        apiHeaders={'Authorization': 'Bearer ' + session['oauth_token']['access_token']}
        resp = requests.get(app.client_details['api_url'] + apiType ,headers=apiHeaders)
        userid=resp.json()['id']
    except:
        return False

    try:
        apiType='projects'
        apiSearchParams={'membership':'true','pagenation':'keyset','per_page': '50000','order_by': 'name','sort':'asc'}
        apiHeaders={'Authorization': 'Bearer ' + session['oauth_token']['access_token']}
        resp = requests.get(app.client_details['api_url'] + apiType ,headers=apiHeaders,params=apiSearchParams)
    except:
        return False

    for projectDetails in resp.json():
        if projectDetails['path_with_namespace'] == session['project']:
            gitlabProjectName = projectDetails['path_with_namespace']
            return True

    return False

##########################
def checkJWT(token):
    jwtSecret = 'ToBeDefinedAsEnvironmentVariable'
    autorized = False

    try:
        jwtSecret = os.getenv('JWT_SECRET')
        decoded_token = jwt.decode(token, jwtSecret, algorithms=['HS256'])
        token_expiration_datetime = datetime.strptime(decoded_token['expiration'], '%Y-%m-%d %H:%M:%S.%f')
        if token_expiration_datetime > datetime.now():
            autorized = True
        else:
            autorized = False
    except:
           return False
    return autorized

##########################
def _generateJWT():
    jwtSecret = 'ToBeDefinedAsEnvironmentVariable'
    secondsToExpiration = 30
    try:
        if 'expiration' in request.args:
            secondsToExpiration = request.args['expiration']
        expiration = datetime.now() + timedelta(seconds=int(secondsToExpiration))
        jwtSecret = os.getenv('JWT_SECRET')
        token = jwt.encode({'expiration': str(expiration)}, jwtSecret, algorithm='HS256')
        returnCode='200'
        isError=False
    except:
        returnCode='400'
        isError=True
        message='Error generating token'
        return jsonify(isError= isError, statusCode= returnCode,data= message), returnCode

    return token.decode("utf-8") 

##########################
@app.route('/hello',methods=['GET']) 
def hello(): 
    return jsonify('Hello','200'),200

##########################
@app.route('/error',methods=['GET']) 
def error(): 
    print("Error - request_type is missing or not supported or something else went wrong")
    return jsonify(request.args['errormsg'],'400'),400

##########################  
if __name__ == "__main__": 
    confDetails()
    app.run(host ='0.0.0.0', port = 5001, debug = True) 
