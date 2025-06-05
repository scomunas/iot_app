######################################
## Get blind state and action it
## 
######################################

from modules import ifttt_app
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

    # Get blind list
    filename = "blind_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    blinds = data.get("blinds")
    # print(blinds)

    response_description = []
    status = 400
    for blind in blinds:
    ## Check if body has the attributes
        if (blind['type'] == "aqara"):
            print("Persiana Aqara, no tiene status")
            status = 200
            response_description.append(
                {
                    "name": blind['name'],
                    "position": -1,
                    "type": blind['type']
                }
            )
        elif (blind['type'] == "shelly"):
            print("Persiana Shelly, obteniendo status")

            # Get shelly token
            filename = "shelly_token.json"
            with open(filename, "r") as f:
                data = json.load(f)
            url_base = data.get("url")
            api_key = data.get("api_key")
            
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
                    response_description.append(
                        {
                            "name": blind['name'],
                            "position": cover_data['current_pos'],
                            "type": blind['type']
                        }
                    )
            else:
                print("Respuesta fallida por parte de Shelly")
                status = 400
                response_description.append(
                    {
                        "name": blind['name'],
                        "position": 0,
                        "type": blind['type']
                    }
                )
        else:
            print("Tipo de persiana no reconocido")
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
        "body": json.dumps(response_description)
    }


## Set blind position or action
## position only for shelly
## aqara only action
def set_blind_position(event, context):
    ## Get Event parameters
    print("Set Blind Position -------------------------------------------")
    # print(event)
    body = json.loads(event["body"])
    print(body)

    # Get blind list
    filename = "blind_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    blinds = data.get("blinds")

   ## Check if body has the attributes
    if ("blind" in body.keys()):
        if ("position" in body.keys()):
            print("Blind movement demanded by position")
            print("Body check OK")

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'shelly'):
                # Get token data
                filename = "shelly_token.json"
                with open(filename, "r") as f:
                    data = json.load(f)
                url_base = data.get("url")
                api_key = data.get("api_key")

                url = url_base + "/device/relay/roller/settings/topos"
                # print(url)
                payload = 'auth_key=' + api_key + '&id=' + blind_id + '&pos=' + body['position']
                # print(payload)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                    }

                response = requests.request("POST", url, headers=headers, data=payload)
                response_json = response.json()

                status = 200
                response_description = f"Persiana {body['blind']} fijada al {body['position']}"
            elif (blind_type == 'aqara'):
                print("Aqara blind cannot be moved by position")
                status = 400
                response_description = 'No puedo mover la persiana Aqara por posición'
            else:
                print("Blind not found")
                status = 400
                response_description = 'No encuentro la persiana'
        elif ("action" in body.keys()):
            print("Blind movement demanded by action")
            print("Body check OK")

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'aqara'):
                print("Persiana Aqara")
                body = {
                        "blind": blind_id,
                        "action": body['action']
                    }
                # print(body)
                ifttt_app(
                    key = "gcs4wieOf6v8rnA-CD8QbK3XP39vs_FIfnjvM-2Y6LA",
                    app_name = "iot_v8_blinds",
                    body = body
                )

                status = 200
                response_description = f"Persiana {body['blind']} accionada para {body['action']}"
            elif (blind_type == 'shelly'):
                print("Persiana Shelly")

                # Get token data
                filename = "shelly_token.json"
                with open(filename, "r") as f:
                    data = json.load(f)
                url_base = data.get("url")
                api_key = data.get("api_key")

                url = url_base + "/device/relay/roller/control"
                # print(url)
                payload = 'auth_key=' + api_key + '&id=' + blind_id + '&direction=' + body['action']
                # print(payload)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                    }

                response = requests.request("POST", url, headers=headers, data=payload)
                response_json = response.json()

                status = 200
                response_description = f"Persiana {body['blind']} accionada para {body['action']}"
            else:
                print("Blind not found")
                status = 400
                response_description = 'No encuentro la persiana'
        else:
            print("Body check KO")
            status = 400
            response_description = 'Petición mal formada'
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
