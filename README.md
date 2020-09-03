# Gitlab extended API

### High-level Description
This project contains the framework for extended functionality of the GitLab API 
which should be exposed to end-users in a form of self-service apis.

End-users which will be authenticated in GitLab, will be able to consume the project-level api 
if they are member of the project with predefine access level
(Access level can be description can be found here: https://docs.gitlab.com/ee/api/access_requests.html)

Authorization to use any of the exposed apis is based on the oauth2 web-application flow.

### Framework Components
- Oauth2 client: adminapi.py 
- Repository hub of APIs declaring : apihub.py
- Specific API implementation: example of `archive project` implementation - archive.py

Note: implementation of these components is in python3 and flask

While the Oauth2 client implementation is a common component for all the apis, 
the repository hub of APIs will need to be extended for each new api, with new declaration,  
and the actual api implementation need to be implemented as a standalone component, which can be invoked through the API declaration


### Register application as oauth2 client
Follow these instructions: https://docs.gitlab.com/ee/integration/oauth_provider.html 

#### Example:
- `archive.py` is a CLI implementation of archiving gitlab project. 
- `/api/v1/archive` is the declaring piece of the archive api which will be exposed to end-users in the api hub: `apihub.py`
- End-point for end-users to consume the api is through the oauth2 client interface, which implemented in `adminapi.py` 


### Deployment components
- Dockerfile `Dockerfile` for buiding application image
- Docker-compose `docker-compose.yaml` for building and testing the application locally
- Helm chart `gitlabapi/Chart.yaml` for deploying the application into openshift

#### Example of deployment steps
- Edit all the oauth2 client details in `oauthclient.properties`
- Expose mandatory environment variables with: 
    - GITLAB_TOKEN : Admin token with api permissions
    - JWT_SECRET : unique random secret
    
        * If running local, use `export GITLAB_TOKEN=...`
        * If running through local docker container, update the values in `docker-compose.yaml`
        * If deploying into openshift, update in the helm chart values file: `gitlabapi/values.yaml`

- Deploy the application:
    * local: `python adminpy.py`
    * docker: `docker-compose build ; docker-compose up`
    * Openshift:
        * local packaging: `docker-compose build ; docker-compose push ; helm package gitalbapi ; helm install gitlabapi gitlabapi-0.1.0.tgz`
        * package from helm repository: `helm pull <your helm repo>/gitlabapi ; helm install gitlabapi gitlabapi-0.1.0.tgz`
          Note: <your helm repo> should be helm repository configured by `helm repo add ...` ; values.yaml will need to be updated with specific client and environment values

#### Example for how to consume the archive api
Note: The application need to be registered in gitlab instance such example.gitlab.com

- Readiness check: https://\<your k8s ingress url\>/hello
- Archive api: https://\<your k8s ingress url\>/gitlabrequest?request_type=archive&project=eransery/test_archive_project 


        



