######################################
## Get blind state and action it
## 
######################################

# from modules import insert_db, get_db
import json
import os
# from datetime import datetime, timedelta
# import pytz
import requests

# You will need a shelly_token.json file in the root with these attributes:
# {
#     "api-key": "xxxxxxxx",
#     "url": "xxxxxxxx",     
    # "blinds": {
    #     "comedor": "xxx",
    #     "estudio": "xxx",
    #     ...
    # }
# }

## Get blind state
## only for shelly
## aqara always return 0 
def get_blind_state(event, context):
    ## Get Event parameters
    print("Get Blind State -------------------------------------------")
    # print(event)
    # params = event["queryStringParameters"]
    # print(params)

    # Get token data
    filename = "shelly_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    url_base = data.get("url")
    api_key = data.get("api_key")
    blinds = data.get("blinds")
    # print(blinds)

    response_description = {}
    status = 400
    for blind in blinds:
    ## Check if body has the attributes
        if (blind['id'] == "aqara"):
            print("Persiana Aqara, no tiene status")
            response_description[blind['name']] = 0
        else:
            print("Persiana Shelly, obteniendo status")
            url = url_base + "/device/status"
            # print(url)
            payload = 'auth_key=' + api_key + '&id=' + blind['id']
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

            response = requests.request("POST", url, headers=headers, data=payload)
            response_json = response.json()
            # print(response_json)

            if (response_json['isok'] == True and
                "data" in response_json.keys()):
                if(response_json['data']['online'] == True):
                    cover_data = response_json['data']['device_status']['cover:0']
                    status = 200
                    response_description[blind['name']] = cover_data['current_pos']
            else:
                print("Respuesta fallida por parte de Shelly")
                status = 400
                response_description[blind['name']] = 0

    print("Status:")
    print(status)
    print("Reponse Description:")
    print(response_description)
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
        },
        "body": json.dumps(response_description)
    }


## Set blind position
## only for shelly
## aqara only 100 for up and rest for down
def set_blind_position(event, context):
    ## TODO
    ## Accept calls for aqara blinds

    ## Get Event parameters
    print("Set Blind Position -------------------------------------------")
    # print(event)
    body = json.loads(event["body"])
    print(body)

    # Get token data
    filename = "shelly_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    url_base = data.get("url")
    api_key = data.get("api_key")
    blinds = data.get("blinds")
    # print(blinds)

   ## Check if body has the attributes
    if ("blind" in body.keys() and
        "position" in body.keys()):
        print("Body check OK")

        # Get blind ID if there is in the list
        id = 'none'
        for blind in blinds:
            if (blind['name'] == body['blind']):
                id = blind['id']

        if ((id != 'none') and (id != "aqara")):
            url = url_base + "/device/relay/roller/settings/topos"
            # print(url)
            payload = 'auth_key=' + api_key + '&id=' + id + '&pos=' + body['position']
            print(payload)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

            response = requests.request("POST", url, headers=headers, data=payload)
            response_json = response.json()

            status = 200
            response_description = f"Persiana {body['blind']} fijada al {body['position']}"
        else:
            print("Blind not found")
            status = 400
            response_description = 'No encuentro la persiana o es aqara'
    else:
        print("Body check KO")
        status = 400
        response_description = 'Petición mal formada'

    print("Status:")
    print(status)
    print("Reponse Description:")
    print(response_description)
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
        },
        "body": response_description
    }
