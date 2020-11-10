'''
Copyright © 2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import json
from botocore.vendored import requests
from connector_response import ConnectorResponse as ConnectorResponse
import traceback
import base64

default_jira_server = "https://issues.apache.org/jira/rest/api/2/project"
jira_get_project_api = "/rest/api/2/project/"
"""
	Authorization Example 
	lets consider  username = ci360connector and password=Password@123
	Now encode ci360connector:Password@123 [username:password] using base64 encoding. After encoding it will look like "Y2kzNjBjb25uZWN0b3I6UGFzc3dvcmRAMTIz"
	Insert encoded string into default_authorization variable below
"""
default_authorization = "<configure-your-base64-endcoded-authorization>"

def lambda_handler(event, context):
    try:
        print("Input event : ", event)
        response = perform_request(event)
        return response.to_dict()
    except Exception as e:
        cr = ConnectorResponse(500, "An error occurred. The JIRA projects could not be populated with the required information.", None, True)
        print("Error", e)
        traceback.print_exc()
        return cr
    
def perform_request(event):
    
    jira_username = ""
    jira_password = ""
    jira_url = ""
    incoming_headers = {}

    #Retrieve headers
    if event is not None :
        if "headers" in event :
            incoming_headers = event["headers"]
            print("Incoming headers : ", incoming_headers)
    
    if incoming_headers is not None: 
        if "jira-url" in incoming_headers:
            jira_url = incoming_headers["jira-url"] + jira_get_project_api
        if "jira-username" in incoming_headers:
            jira_username = incoming_headers["jira-username"]
        if "jira-password" in incoming_headers:
            jira_password = incoming_headers["jira-password"]
        
    if jira_url == "" or jira_url is None :
        jira_url =  default_jira_server + jira_get_project_api
        print("using dafault jira server")   
                    
    print("Jira url : ", jira_url)
    print("Jira username : ", jira_username)
    
    if jira_url == (default_jira_server + jira_get_project_api):
        authorization = 'Basic %s' %  default_authorization
        print("using default credentials for authorization")
    else:
        authorization = 'Basic %s' %  base64.b64encode(bytes(jira_username + ':' + jira_password, "utf-8")).decode("utf-8")
        print("encoding authorization headers completed")
        
    print("authorization : ", authorization)
    
    if incoming_headers is None:
        incoming_headers = {}
    incoming_headers['Authorization'] = authorization
    incoming_headers['Content-Type'] = 'application/json'
    
    response = requests.get(jira_url)
    
    if response.status_code == 200:
        return create_response(response.json())
    else:
        cr = ConnectorResponse(response.status_code, "The JIRA projects could not be populated with the required information. The specified JIRA URL, user name, and the password can either be unavailable or invalid. Specify valid values.", None, True)
        print("Error", cr)
        traceback.print_exc()    
       

def create_response(response_json):
    ret_val = {
        "dataProvider": []
    }

    for project in response_json:
        resp = {}
        resp["key"] = project['key']
        resp["text"] = project['key']
        ret_val["dataProvider"].append(resp)

    cr = ConnectorResponse(200, json.dumps(ret_val))     
    print("Response ", cr.to_dict())
        
    return cr    
    
def send_validation_error(error_string):
    print(error_string)
    return ConnectorResponse(400, error_string, None, True)