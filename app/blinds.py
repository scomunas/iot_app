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
    get_aqara_device_state,
    set_aqara_roller_action
)
import json

## Get all blind state
## only for shelly
## aqara always return 0 
def get_blind_state(event, context):
    ## Get Event parameters
    print("|-0-| Get Blind State")
    print("|-0-| No event parameters needed")

    # Get blind list
    blinds = get_blind_list()
    print(f"|-0-| Blind list obtained: {blinds}")

    ## Get shelly status ------------------------------------------------------
    print("|-0-| Getting Shelly blinds status")

    # Get id list
    device_ids = []
    for blind in blinds:
        if (blind['type'] == "shelly"):
            device_ids.append(blind['id'])
    print(f"|-0-| Device ids: {device_ids}")
    
    # Get shelly token
    api_key, url = get_shelly_token()
    print("|-0-| Shelly token obtained")
    
    # Get device status
    shelly_status = get_shelly_device_state(
        device_list=device_ids,
        api_key=api_key,
        url_base=url
    )
    print(f"|-0-| Device status: {shelly_status}")

    # Add names to response
    for blind in shelly_status:
        for blind_data in blinds:
            if (blind['id'] == blind_data['id']):
                blind['name'] = blind_data['name']
    print(f"|-0-| Device status updated: {shelly_status}")

    ## Get Aqara status ------------------------------------------------------
    print("|-0-| Getting Aqara blinds status")

    # Get id list
    device_ids = []
    for blind in blinds:
        if (blind['type'] == "aqara"):
            device_ids.append(blind['id'])
    print(f"|-0-| Device ids: {device_ids}")

    # Get device status
    aqara_status = get_aqara_device_state(
        device_list=device_ids,
        api_key="",
        url_base=""
    )
    print(f"|-0-| Device status: {aqara_status}")

    # Add names to response
    for blind in aqara_status:
        for blind_data in blinds:
            if (blind['id'] == blind_data['id']):
                blind['name'] = blind_data['name']
    print(f"|-0-| Device status updated: {aqara_status}")

    # Join all results ---------------------------------------
    blinds_status = shelly_status + aqara_status
    if (len(blinds_status) > 0):
        status = 200
        response_description = blinds_status
    else:
        status = 400
        response_description = []

    print(f"|-0-| Status: {status}")
    print(f"|-0-| Reponse Description: {response_description}")
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
    print("|-0-| Set Blind Position")
    body = json.loads(event["body"])
    print(f"|-0-| Body: {body}")

   ## Check if body has the attributes
    if ("blind" in body.keys()):
        if ("position" in body.keys()):
            print("|-0-| Blind movement demanded by position")
            print("|-0-| Body check OK")

            # Get blind list
            blinds = get_blind_list()
            print(f"|-0-| Light list obtained: {blinds}")

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'shelly'):
                print("|-0-| Shelly blind")

                # Get token data
                api_key, url = get_shelly_token()
                print("|-0-| Token obtained")

                # Set roller position
                response = set_shelly_roller_position(
                    device_id=blind_id,
                    url_base=url,
                    api_key=api_key,
                    position=body['position']
                )
                print(f"|-0-| Response for action: {response}")

                status = 200
                response_description = f"Blind {body['blind']} fixed to {body['position']}"
            elif (blind_type == 'aqara'):
                print("|-0-| Aqara blind cannot be moved by position")
                status = 400
                response_description = 'Aqara blind cannot be moved by position'
            else:
                print("Blind not found")
                status = 400
                response_description = 'Blind not found'
        elif ("action" in body.keys()):
            print("|-0-| Blind movement demanded by action")
            print("|-0-| Body check OK")

            # Get blind list
            blinds = get_blind_list()
            print(f"|-0-| Light list obtained: {blinds}")

            # Get blind ID if there is in the list
            blind_id = 'none'
            for blind in blinds:
                if (blind['name'] == body['blind']):
                    blind_id = blind['id']
                    blind_type = blind['type']

            if (blind_type == 'aqara'):
                print("|-0-| Aqara blind")

                # Get aqara token
                api_key = get_aqara_token()
                print("|-0-| Token obtained")

                # Set aqara action
                response = set_aqara_roller_action(
                    device_id=blind_id,
                    api_key=api_key,
                    action=body['action']
                )
                print(f"|-0-| Response for action: {response}")

                status = 200
                response_description = f"Blind {body['blind']} set for {body['action']}"
            elif (blind_type == 'shelly'):
                print("|-0-| Shelly blind")

                # Get token data
                api_key, url = get_shelly_token()
                print("|-0-| Token obtained")

                # Set shelly action
                response = set_shelly_roller_action(
                    device_id=blind_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )
                print(f"|-0-| Response for action: {response}")

                status = 200
                response_description = f"Blind {body['blind']} set for {body['action']}"
            else:
                print("|-0-| Blind not found")
                status = 400
                response_description = 'Blind not found'
        else:
            print("|-0-| Body check KO")
            status = 400
            response_description = 'Body check KO'
    else:
        print("|-0-| Body check KO")
        status = 400
        response_description = 'Body check KO'

    print(f"|-0-| Status: {status}")
    print(f"|-0-| Reponse Description: {response_description}")
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
