'''
Copyright © 2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import json
from botocore.vendored import requests
from connector_response import ConnectorResponse as ConnectorResponse
import traceback
import base64

default_url="<configure-your-MSTeams-IncomingWebhook-url>"
    
def perform_request(event, input_data):
    msteams_url = ""
    msteams_comment = ""
    object_name = ""
    user_name = ""
    incoming_headers = {}
         
    #Retrieve user comment - is design center object or plan object
    if "customAttributes" in input_data:
        groups = input_data["customAttributes"]["groups"]
    elif "groupedAttributesRep" in input_data:
        groups = input_data["groupedAttributesRep"]["groups"]
    
    for group in groups:
        for item in group["fields"]:
            if "attributeName" and "value" in item:
                if item["attributeName"] == "MSTeamComment":
                    msteams_comment = item["value"]
        
    print("User comment : ", msteams_comment)
    
    if not msteams_comment:
        return send_validation_error("You must specify a non-blank comment that you want to add to the Microsoft Teams channel.")
    
    #Retrieve headers
    try:
        if event is not None :
            if "headers" in event :
                incoming_headers = event["headers"]
                print("Incoming headers : ", incoming_headers)
        
        if incoming_headers is not None:
            if "msteams-channel-url" in incoming_headers:
                msteams_url = incoming_headers["msteams-channel-url"]
            if "user_id" in incoming_headers:
                user_name = incoming_headers["user_id"]
                print("User name before decode : ", user_name)
                decoded_user_name = base64.b64decode(user_name)
                user_name = decoded_user_name.decode("utf-8")
                print("User name after decode : ", user_name)    
    except Exception as e:
        cr = ConnectorResponse(500, "An error occurred. Your request could not be processed.", None, True)
        print("Error", e)
        traceback.print_exc()
        return cr
    
    if msteams_url == "" or msteams_url is None :
        msteams_url = default_url
    if user_name == "" or user_name is None :
        user_name = "Alice"
        print("User name not configured in the headers. Setting default user name as 'Alice' ")
                        
    print("MSTeams channel url : ", msteams_url)            
    print("User Name : ", user_name)
    
    if "name" in input_data :       
        object_name = input_data["name"]
    print("Object name : ", object_name)                
    if not object_name:
        return send_validation_error("You must specify a non-blank object name.")
        
    body = {"@type": "MessageCard",
        "themeColor": "0072C6",
        "title": "Comment added on <b>" + object_name + "</b>",
        "text": "By <b>" + user_name + "</b>",
        "sections": [{
            "activityTitle": ""+msteams_comment,
            "activitySubtitle": "Please login to [SAS CI 360](https://www.sas.com/en_us/software/customer-intelligence-360.html) for more details",
            "activityImage": "https://i.ibb.co/hMyMJ6S/Galaxy.png",
            "markdown": 'true'
        }]
    }

    response = requests.post(msteams_url, data=json.dumps(body))
        
    if response.status_code == 200:
        cr = ConnectorResponse(200, json.dumps({"message":"Comment Posted In MSTeams Channel"}))
    else:
        cr = ConnectorResponse(response.status_code, "The comment could not be added to the Microsoft Teams channel. The specified channel URL and parameter values are either invalid or unavailable. Specify valid values.", None, True)
        print("Error", cr)
        traceback.print_exc()    
        
    print("Response", cr.to_dict())
        
    return cr;
    
def lambda_handler(event, context):
    try:
        print("Input event : ", event)
        
        body = json.loads(event["body"]);
        print("Input body : ", body)

        response = perform_request(event, body)
        print(response.to_dict())
        return response.to_dict()
    except Exception as e:
        cr = ConnectorResponse(500, "An error occurred. The comment could not be added to the Microsoft Teams channel.", None, True)
        print("Error", e)
        traceback.print_exc()
        return cr
        
def send_validation_error(error_string):
    print(error_string)
    return ConnectorResponse(400, error_string, None, True)