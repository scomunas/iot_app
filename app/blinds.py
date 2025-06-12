######################################
## Get blind state and action it
## 
######################################

from modules import (
    get_blind_list,
    get_shelly_token,
    get_shelly_device_state,
    set_shelly_roller_position,
    set_shelly_roller_action,
    get_aqara_token,
    set_aqara_roller_action
)
import json

## Get all blind state
## only for shelly
## aqara always return 0 
def get_blind_state(event, context):
    ## Get Event parameters
    print("Get Blind State -------------------------------------------")

    # Get blind list
    blinds = get_blind_list()
    print(blinds)

    # Get status from each blind
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
                    "type": blind['type'],
                    "online": True
                }
            )
        elif (blind['type'] == "shelly"):
            print("Persiana Shelly, obteniendo status")

            # Get shelly token
            api_key, url = get_shelly_token()
            
            # Get device status
            response = get_shelly_device_state(
                device_id=blind['id'],
                api_key=api_key,
                url_base=url
            )

            # Check Shelly response
            if (response['isok'] == True and
                "data" in response.keys()):
                if(response['data']['online'] == True):
                    cover_data = response['data']['device_status']['cover:0']
                    status = 200
                    response_description.append(
                        {
                            "name": blind['name'],
                            "position": cover_data['current_pos'],
                            "type": blind['type'],
                            "online": True
                        }
                    )                     
                else:
                    status = 200
                    response_description.append(
                        {
                            "name": blind['name'],
                            "position": -1,
                            "type": blind['type'],
                            "online": False
                        }
                    )
            else:
                print("Shelly response KO")
                status = 400
                response_description.append(
                    {
                        "name": blind['name'],
                        "position": 0,
                        "type": blind['type'],
                        "online": False
                    }
                )
        else:
            print("Body is KO")
            status = 400
            response_description = 'Body is KO'

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
## position or action for shelly
## aqara only action
def set_blind_position(event, context):
    ## Get Event parameters
    print("Set Blind Position -------------------------------------------")
    # print(event)
    body = json.loads(event["body"])
    print(body)

   ## Check if body has the attributes
    if ("blind" in body.keys()):
        if ("position" in body.keys()):
            print("Blind movement demanded by position")
            print("Body check OK")

            # Get blind list
            blinds = get_blind_list()

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'shelly'):
                # Get token data
                api_key, url = get_shelly_token()

                # Set roller position
                response = set_shelly_roller_position(
                    device_id=blind_id,
                    url_base=url,
                    api_key=api_key,
                    position=body['position']
                )

                status = 200
                response_description = f"Blind {body['blind']} fixed to {body['position']}"
            elif (blind_type == 'aqara'):
                print("Aqara blind cannot be moved by position")
                status = 400
                response_description = 'Aqara blind cannot be moved by position'
            else:
                print("Blind not found")
                status = 400
                response_description = 'Blind not found'
        elif ("action" in body.keys()):
            print("Blind movement demanded by action")
            print("Body check OK")

            # Get blind list
            blinds = get_blind_list()

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'aqara'):
                print("Persiana Aqara")

                # Get aqara token
                api_key = get_aqara_token()

                # Set aqara action
                response = set_aqara_roller_action(
                    device_id=blind_id,
                    api_key=api_key,
                    action=body['action']
                )

                status = 200
                response_description = f"Blind {body['blind']} set for {body['action']}"
            elif (blind_type == 'shelly'):
                print("Persiana Shelly")

                # Get token data
                api_key, url = get_shelly_token()

                # Set shelly action
                repsons_json = set_shelly_roller_action(
                    device_id=blind_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )

                status = 200
                response_description = f"Blind {body['blind']} set for {body['action']}"
            else:
                print("Blind not found")
                status = 400
                response_description = 'Blind not found'
        else:
            print("Body check KO")
            status = 400
            response_description = 'Body check KO'
    else:
        print("Body check KO")
        status = 400
        response_description = 'Body check KO'

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
