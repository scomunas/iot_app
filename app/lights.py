######################################
## Get blind state and action it
## 
######################################

from modules import (
    get_light_list,
    get_shelly_token,
    get_shelly_device_state,
    set_shelly_light_action,
    get_govee_token,
    get_govee_light_status,
    set_govee_light_action
)
import json

## Get all light state
## only for shelly
def get_light_state(event, context):
    ## Get Event parameters
    print("|-0-| Get Light State")
    print("|-0-| No event parameters needed")

    # Get lights list
    lights = get_light_list()
    print(f"|-0-| Light list obtained: {lights}")

    # Get shelly status ------------------------------------------------------
    print("|-0-| Getting Shelly lights status")

    # Get id list
    device_ids = []
    for light in lights:
        if (light['type'] == "shelly"):
            device_ids.append(light['id'])
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
    for light in shelly_status:
        for light_data in lights:
            if (light['id'] == light_data['id']):
                light['name'] = light_data['name']
    print(f"|-0-| Device status updated: {shelly_status}")

    # Get Govee status ------------------------------------------------------
    print("|-0-| Getting Govee lights status")

    # Get govee token
    api_key, url = get_govee_token()
    print("|-0-| Govee token obtained")

    # Get id list
    device_ids = []
    for light in lights:
        if (light['type'] == "govee"):
            device_ids.append(light['id'])
    print(f"|-0-| Device ids: {device_ids}")

    # Get device status
    govee_status = get_govee_light_status(
        device_list=device_ids,
        api_key=api_key,
        url_base=url
    )
    print(f"|-0-| Device status: {govee_status}")

    # Add names to response
    for light in govee_status:
        for light_data in lights:
            if (light['id'] == light_data['id']):
                light['name'] = light_data['name']
    print(f"|-0-| Device status updated: {govee_status}")
 
    # Join all results ---------------------------------------
    lights_status = shelly_status + govee_status
    if (len(lights_status) > 0):
        status = 200
        response_description = lights_status
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


## Set light action
def set_light_action(event, context):
    ## Get Event parameters
    print("|-0-| Set Light Action")
    body = json.loads(event["body"])
    print(f"|-0-| Body: {body}")

   ## Check if body has the attributes
    if ("light" in body.keys()):
        if ("action" in body.keys()):
            print("|-0-| Light action demanded")
            print("|-0-| Body check OK")

            # Get lights list
            lights = get_light_list()
            print(f"|-0-| Light list obtained: {lights}")

            # Get light ID if there is in the list
            light_id = 'none'
            for light in lights:
                if (light['name'] == body['light']):
                    light_id = light['id']
                    light_type = light['type']

            if (light_type == 'govee'):
                print("|-0-| Govee light")

                # Get token data
                api_key, url = get_govee_token()
                print("|-0-| Token obtained")

                # Set govee action
                response = set_govee_light_action(
                    device_id=light_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )
                print(f"|-0-| Response for action: {response}")

                # Set final response
                status = 200
                response_description = f"Light {body['light']} set for {body['action']}"
            elif (light_type == 'shelly'):
                print("|-0-| Shelly light")

                # Get token data
                api_key, url = get_shelly_token()
                print("|-0-| Token obtained")

                # Set shelly action
                response = set_shelly_light_action(
                    device_id=light_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )
                print(f"|-0-| Response for action: {response}")

                status = 200
                response_description = f"Light {body['light']} set for {body['action']}"
            else:
                print("|-0-| Token obtained")
                status = 400
                response_description = 'Light not found'
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
