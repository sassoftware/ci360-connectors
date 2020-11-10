'''
Copyright © 2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import json
from botocore.vendored import requests
from connector_response import ConnectorResponse as ConnectorResponse
import traceback
import base64

default_jira_server =  "https://issues.apache.org/jira"
jira_get_project_api = "/rest/api/2/project/"
default_authorization = "<configure-your-base64-endcoded-authorization>" 
"""
Authorization Example 
consider  username = ci360connector and password=Password@123
Now encode ci360connector:Password@123 using base64 encoding. It looks like "Y2kzNjBjb25uZWN0b3I6UGFzc3dvcmRAMTIz"
Insert this encoded string into default_authorization variable
"""


def lambda_handler(event, context):
    try:
        print("Input event : ", event)
        response = perform_request(event)
        return response.to_dict()
    except Exception as e:
        cr = ConnectorResponse(500, "An error occurred. The information about the JIRA project could not be retrieved.", None, True)
        print("Error", e)
        traceback.print_exc()
        return cr
    
def perform_request(event):
    
    jira_username = ""
    jira_password = ""
    jira_url = ""
    project_key = ""
    body = ""
    incoming_headers = {}

    body = json.loads(event["body"]);
    print("Input body : ", body)
    #Retrieve user comment - is design center object or plan object
    if "customAttributes" in body:
        groups = body["customAttributes"]["groups"]
    elif "groupedAttributesRep" in body:
        groups = body["groupedAttributesRep"]["groups"]
    
    print("groups : ", groups)
    for group in groups:
        for item in group["fields"]:
            if "attributeName" and "value" in item:
                if item["attributeName"] == "JiraProjectKey":
                    project_key = item["value"]
    
    print("Project key : ", project_key)
    
    if not project_key:
        return send_validation_error("You must specify a non-blank ID for the JIRA project.")
    
    #Retrieve headers
    if event is not None :
        if "headers" in event :
            incoming_headers = event["headers"]
            print("Incoming headers : ", incoming_headers)
    
    if incoming_headers is not None: 
        if "jira-url" in incoming_headers:
            jira_url = incoming_headers["jira-url"] + jira_get_project_api + project_key
        if "jira-username" in incoming_headers:
            jira_username = incoming_headers["jira-username"]
        if "jira-password" in incoming_headers:
            jira_password = incoming_headers["jira-password"]
        
    if jira_url == "" or jira_url is None :
        jira_url =  default_jira_server + jira_get_project_api + project_key
        print("using dafault jira server")   
                    
    print("Jira url : ", jira_url)
    print("Jira username : ", jira_username)
    
    if jira_url == (default_jira_server + jira_get_project_api + project_key):
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

    body = {
          "jql": "text ~ \""+project_key+"\"",
          "maxResults": 5,
          "startAt": 0
        }
    
    response = requests.get(jira_url, data = json.dumps(body), headers=incoming_headers)
     
    if response.status_code == 200:
        cr = ConnectorResponse(200, json.dumps(response.json()))
    else:
        cr = ConnectorResponse(response.status_code, "The information about the JIRA project '" + project_key + "' could not be retrieved. The specified JIRA URL, user name, and the password can either be unavailable or invalid. Specify valid values.", None, True)
        print("Error", cr)
        traceback.print_exc()    
        
    print("Response", cr.to_dict())
        
    return cr;
  
def send_validation_error(error_string):
    print(error_string)
    return ConnectorResponse(400, error_string, None, True)