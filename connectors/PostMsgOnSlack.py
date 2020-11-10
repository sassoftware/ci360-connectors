'''
Copyright © 2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import json
from botocore.vendored import requests
from connector_response import ConnectorResponse as ConnectorResponse
import traceback
import base64

default_url="<configure-your-Slack-Webhook-url>"
    
def perform_request(event, input_data):
    slack_url = ""
    slack_comment = ""
    object_name = ""
    user_name = ""
         
    #Retrieve user comment - is design center object or plan object
    if "customAttributes" in input_data:
        groups = input_data["customAttributes"]["groups"]
    elif "groupedAttributesRep" in input_data:
        groups = input_data["groupedAttributesRep"]["groups"]
    
    for group in groups:
        for item in group["fields"]:
            if "attributeName" and "value" in item:
                if item["attributeName"] == "SlackComment":
                    slack_comment = item["value"]
        
    print("User comment : ", slack_comment)
    if not slack_comment:
        return send_validation_error("You must specify a non-blank comment that you want to add to the Slack channel.")
        
    #Retrieve headers
    try:
        if event is not None :
            if "headers" in event :
                incoming_headers = event["headers"]
                print("Incoming headers : ", incoming_headers)
        
        if incoming_headers is not None:
            if "slack-channel-url" in incoming_headers:
                slack_url = incoming_headers["slack-channel-url"]
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
    
    if slack_url == "" or slack_url is None :
        slack_url = default_url
    if user_name == "" or user_name is None :
        user_name = "Alice"
        print("User name not configured in the headers. Setting default user name as 'Alice' ")
                            
    print("Slack channel url : ", slack_url)      
    print("User Name : ", user_name)
    
    if "name" in input_data :        
        object_name = input_data["name"]
    print("Object name : ", object_name)
    if not object_name:
        return send_validation_error("You must specify a non-blank object name.")
        
    body = {
        "blocks": [
            {
                "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Comment added on *" + object_name + "*\n\n By *" + user_name + "*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "" + slack_comment + "\n Please login to <https://www.sas.com/en_us/software/customer-intelligence-360.html|SAS CI360> for more details"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://i.ibb.co/hMyMJ6S/Galaxy.png",
                        "alt_text": "Connector"
                    }
            }
        ]
    }
        
    response = requests.post(slack_url, data=json.dumps(body))
   
    if response.status_code == 200:
        cr = ConnectorResponse(200, json.dumps({"message":"Comment Posted In Slack Channel"}))
    else:
        cr = ConnectorResponse(response.status_code, "The comment could not be added to the Slack channel. The specified channel URL and parameter values are either invalid or unavailable. Specify valid values.", None, True)
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
        cr = ConnectorResponse(500, "An error occurred. The comment could not be added to the Slack channel.", None, True)
        print("Error", e)
        traceback.print_exc()
        return cr
        
def send_validation_error(error_string):
    print(error_string)
    return ConnectorResponse(400, error_string, None, True)