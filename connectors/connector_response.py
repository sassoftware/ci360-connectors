'''
Copyright © 2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import json

json_headers = {
    'content-type': "application/json"
}

class ConnectorResponse:
    

    def __init__(self, statusCode=None, body=None, headers=None, isError=False):        
        self.statusCode = statusCode
        if isError:
            self.body = json.dumps(ConnectorResponseBody(body, statusCode).to_dict())
        else:
            self.body = body
            
        if headers:
            self.headers = headers
        else:
            self.headers = json_headers

    def to_dict(self):
        return self.__dict__


class ConnectorResponseBody:

    def __init__(self, message=None,httpStatusCode=None):        
        self.message = message
        self.httpStatusCode = httpStatusCode

    def to_dict(self):
        return self.__dict__