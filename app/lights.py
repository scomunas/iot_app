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
    # TODO
    # Añadir luces de otros fabricantes

    ## Get Event parameters
    print("Get Light State -------------------------------------------")

    # Get lights list
    lights = get_light_list()
    print(lights)

    # Get status from each blind
    response_description = []
    status = 400
    for light in lights:
    ## Check if body has the attributes
        if (light['type'] == "govee"):
            print("Luz Govee, obteniendo statusatus")

            # Get govee token
            api_key, url = get_govee_token()
            
            # Get device status
            response = get_govee_light_status(
                device_id=light['id'],
                api_key=api_key,
                url_base=url
            )

            # Check Govee response
            if (response['code'] == 200 and
                "payload" in response.keys()):
                # Look for capabilities
                govee_online = False
                govee_on_off = 0
                for capability in response['payload']['capabilities']:
                    if (capability['instance'] == 'online'):
                        govee_online = capability['state']['value']
                    if (capability['instance'] == 'powerSwitch'):
                        govee_on_off = capability['state']['value']
                if(govee_online == True):
                    if(govee_on_off == 1):
                        light_data = True
                    else:
                        light_data = False
                status = 200
                response_description.append(
                    {
                        "name": light['name'],
                        "status": light_data,
                        "type": light['type'],
                        "online": govee_online
                    }
                )
            else:
                print("Govee response KO")
                status = 400
                response_description.append(
                    {
                        "name": light['name'],
                        "status": False,
                        "type": light['type'],
                        "online": False
                    }
                )
        elif (light['type'] == "shelly"):
            print("Luz Shelly, obteniendo status")

            # Get shelly token
            api_key, url = get_shelly_token()
            
            # Get device status
            response = get_shelly_device_state(
                device_id=light['id'],
                api_key=api_key,
                url_base=url
            )

            # Check Shelly response
            if (response['isok'] == True and
                "data" in response.keys()):
                shelly_online = response['data']['online'] 
                if(shelly_online== True):
                    # Check depends on version, if has relays or switch
                    if ("relays" in response['data']['device_status'].keys()):
                        light_data = response['data']['device_status']['relays'][0]['ison']
                    elif ("switch:0" in response['data']['device_status'].keys()):
                        light_data = response['data']['device_status']['switch:0']['output']
                    else:
                        light_data = 'error'
                    status = 200
                    response_description.append(
                        {
                            "name": light['name'],
                            "status": light_data,
                            "type": light['type'],
                            "online": shelly_online
                        }
                    )
                else:
                    status = 200
                    response_description.append(
                        {
                            "name": light['name'],
                            "status": False,
                            "type": light['type'],
                            "online": shelly_online
                        }
                    )
            else:
                print("Shelly response KO")
                status = 400
                response_description.append(
                    {
                        "name": light['name'],
                        "status": False,
                        "type": light['type'],
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


## Set light action
def set_light_action(event, context):
    ## Get Event parameters
    print("Set Light Action -------------------------------------------")
    # print(event)
    body = json.loads(event["body"])
    print(body)

   ## Check if body has the attributes
    if ("light" in body.keys()):
        if ("action" in body.keys()):
            print("Light action demanded")
            print("Body check OK")

            # Get lights list
            lights = get_light_list()
            print(lights)

            # Get light ID if there is in the list
            light_id = 'none'
            for light in lights:
                if (light['name'] == body['light']):
                    light_id = light['id']
                    light_type = light['type']

            if (light_type == 'govee'):
                print("Luz Govee")

                # Get token data
                api_key, url = get_govee_token()

                # Set govee action
                repsons_json = set_govee_light_action(
                    device_id=light_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )

                status = 200
                response_description = f"Light {body['light']} set for {body['action']}"
            elif (light_type == 'shelly'):
                print("Luz Shelly")

                # Get token data
                api_key, url = get_shelly_token()

                # Set shelly action
                repsons_json = set_shelly_light_action(
                    device_id=light_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )

                status = 200
                response_description = f"Light {body['light']} set for {body['action']}"
            else:
                print("Light not found")
                status = 400
                response_description = 'Light not found'
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
