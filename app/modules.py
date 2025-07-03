######################################
## Modules
## 
## General functions for use in 
## all lambdas
######################################

# Libraries needed
import json
from datetime import datetime, timedelta
import boto3
import os
import requests
import pytz
import base64

## Insert event row on DB
def insert_db(table_name, event_parameters, ttl_days):
    # Calculate dates assuming
    # event date is just now
    CET = pytz.timezone("Europe/Madrid")
    date = datetime.now().astimezone(CET)
    date_delta = date + timedelta(days = ttl_days)
    date_string = date.strftime("%Y%m%d_%H%M%S")
    date_ttl = int(date_delta.timestamp())
    event_parameters['event_date'] = date_string
    event_parameters['event_date_ttl'] = date_ttl
    # print(date_string)

    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Put the row in the table
    response = table.put_item(
        Item = event_parameters
        )
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    # Return status value
    return status_code, response['ResponseMetadata']

# Get results from table
def get_db(table_name):
    dynamodb = boto3.resource('dynamodb')

    # Reference the table
    table = dynamodb.Table(table_name)

    # Perform the scan
    response = table.scan()
    items = response.get('Items', [])
    print(f"Retrieved {len(items)} items.")

    # Handle paginated results (if table has more than 1MB of data)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
        print(f"Retrieved {len(items)} items so far...")

    return items

# Use a IFTTT app
def ifttt_app(key, app_name, body):
    url = "https://maker.ifttt.com/trigger/APPLET_NAME/json/with/key/".replace("APPLET_NAME", app_name) + key
    # print(url)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request('POST', url,
                headers=headers,
                data=json.dumps(body))

    return response.status_code

# Get Netatmo token
def get_netatmo_token():
    # Not inserted in Secrets Manager for budget reasons
    # You will need a netatmo_token.json file in the root with these attributes:
    # {
    #     "CLIENT_ID": "xxxxxxxx",
    #     "CLIENT_SECRET": "xxxxxxxxxxxxx",
    #     "REFRESH_TOKEN": "xxxxxxxxxxxxxxxxx"
    # }

    # Get token data
    filename = "netatmo_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    CLIENT_ID = data.get("CLIENT_ID")
    CLIENT_SECRET = data.get("CLIENT_SECRET")
    REFRESH_TOKEN = data.get("REFRESH_TOKEN")

    # Get new acces_token
    print("Getting token from Netatmo")
    url = 'https://api.netatmo.com/oauth2/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    token_info = response.json()
    access_token = token_info['access_token']
    new_refresh_token = token_info['refresh_token']

    return access_token

# Get netatmo data from all sensors
def get_netatmo_data(access_token):
   # Get data from all the sensors
    url = 'https://api.netatmo.com/api/getstationsdata'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    stations = data['body']['devices']
    module_data = []
    for station in stations:
        station_name = station['station_name']
        if 'dashboard_data' in station:
            temperature = station['dashboard_data'].get('Temperature')
            if temperature is not None:
                module_data.append({
                    "sensor": station_name,
                    "temperature": str(temperature)
                })
        for module in station.get('modules', []):
            module_name = module.get('module_name')
            temperature = module.get('dashboard_data', {}).get('Temperature')
            if temperature is not None:
                module_data.append({
                    "sensor": module_name,
                    "temperature": str(temperature)
                })
        
    return module_data

# Get token for use with Shelly API
def get_shelly_token():
    # You will need a shelly_token.json file in the root with these attributes:
    # {
    #     "api-key": "xxxxxxxx",
    #     "url": "xxxxxxxx",     
    # }

    # Get shelly token
    filename = "shelly_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    url_base = data.get("url")
    api_key = data.get("api_key")

    return api_key, url_base

# Get state from one Shelly device
def get_shelly_device_state(device_list, url_base, api_key):
    url = url_base + "/v2/devices/api/get?auth_key=" + api_key
    payload = json.dumps({
        "ids": device_list,
        "select": [
            "status",
        ],
        "pick": {
            "status": [
                "switch:0",
                "relays",
                "input:0",
                "cover:0"
            ]
        }
        })
    # print(payload)
    headers = {
        'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())

    response_description = []
    # Check Shelly response
    for device in response.json():
        if ("status" in device.keys()):
            shelly_online = device['online'] 
            if(shelly_online == 1):
                # Check depends on version, if has relays or switch
                if ("relays" in device['status'].keys()):
                    device_status = device['status']['relays'][0]['ison']
                elif ("switch:0" in device['status'].keys()):
                    device_status = device['status']['switch:0']['output']
                elif ("cover:0" in device['status'].keys()):
                    device_status = device['status']['cover:0']['current_pos']
                elif ("input:0" in device['status'].keys()):
                    device_status = device['status']['input:0']
                else:
                    device_status = 'error'
                response_description.append(
                    {
                        "id": device['id'],
                        "status": device_status,
                        "type": "shelly",
                        "online": True
                    }
                )
            else:
                response_description.append(
                    {
                        "id": device['id'],
                        "status": False,
                        "type": "shelly",
                        "online": False
                    }
                )
        else:
            response_description.append(
                {
                    "id": device['id'],
                    "status": False,
                    "type": "shelly",
                    "online": False
                }
            )
    
    return response_description

# Set position for a Shelly roller
def set_shelly_roller_position(device_id, url_base, api_key, position):
    url = url_base + "/device/relay/roller/settings/topos"
    # print(url)
    payload = 'auth_key=' + api_key + '&id=' + device_id + '&pos=' + position
    # print(payload)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    
    return response_json

#Set action (open/close/stop) for a Shelly roller
def set_shelly_roller_action(device_id, url_base, api_key, action):
    url = url_base + "/v2/devices/api/set/cover?auth_key=" + api_key
    # print(url)
    payload = json.dumps({
        "id": device_id,
        "channel": 0,
        "position": action
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response

#Set action (on/off) for a Shelly Light
def set_shelly_light_action(device_id, url_base, api_key, action):
    url = url_base + "/v2/devices/api/set/switch?auth_key=" + api_key
    # print(url)
    payload = json.dumps({
        "id": device_id,
        "channel": 0,
        "on": action == "on"
        })
    # print(payload)
    headers = {
        'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response

# Get token for use with Aqara API (for the moment with IFTTT)
def get_aqara_token():
    # You will need a ifttt_token.json file in the root with these attributes:
    # {
    #     "api-key": "xxxxxxxx"
    # }

    # Get ifttt token
    filename = "ifttt_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    api_key = data.get("api_key")

    return api_key

# Get state from one Aqara device
def get_aqara_device_state(device_list, url_base, api_key):
    # No API for Aqara
    response_description = []
    for id in device_list:
        response_description.append(
            {
                "id": id,
                "status": -1,
                "type": "aqara",
                "online": True
            })
        
    return response_description    

# Set action (open/close/stop) for an aqara roller
# Uses ifttt_app function
def set_aqara_roller_action(device_id, api_key, action):
    body = {
            "blind": device_id,
            "action": action
        }
    # print(body)
    ifttt_app(
        key = api_key,
        app_name = "iot_v8_blinds",
        body = body
    )

    return "ok"

# Get token for use with Aqara API (for the moment with IFTTT)
def get_govee_token():
    # You will need a govee_token.json file in the root with these attributes:
    # {
    #     "api-key": "xxxxxxxx",
    #     "url": "xxxxxxxx"
    # }

    # Get ifttt token
    filename = "govee_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    url_base = data.get("url")
    api_key = data.get("api_key")

    return api_key, url_base

# Get state from one Shelly device
def get_govee_light_status(device_list, url_base, api_key):
    url = url_base + "/router/api/v1/device/state"
    headers = {
        'Govee-API-Key': api_key,
        'Content-Type': 'application/json' 
        }
    
    response_description = []
    # Get all light status
    for id in device_list:
        sku, device = id.split("|")
        request_id = sku + datetime.now().strftime("%d%m%Y%H%M%S")
        payload = json.dumps({
            "requestId": request_id,
            "payload": {
                "sku": sku,
                "device": device
            }
        })
        response = requests.request("POST", url, headers=headers, data=payload)
        response_json = response.json()
        # print(response_json)

        if (response_json['code'] == 200 and
            "payload" in response_json.keys()):
            # Look for capabilities
            govee_online = False
            govee_on_off = 0
            for capability in response_json['payload']['capabilities']:
                if (capability['instance'] == 'online'):
                    govee_online = capability['state']['value']
                if (capability['instance'] == 'powerSwitch'):
                    govee_on_off = capability['state']['value']
            if(govee_online == True):
                if(govee_on_off == 1):
                    light_data = True
                else:
                    light_data = False
            response_description.append(
                {
                    "id": id,
                    "status": light_data,
                    "type": "govee",
                    "online": govee_online
                }
            )
        else:
            response_description.append(
                {
                    "id": id,
                    "status": False,
                    "type": "govee",
                    "online": False
                }
            )

    return response_description

# Set action (on/off) for a Shelly Light
def set_govee_light_action(device_id, url_base, api_key, action):
    url = url_base + "/router/api/v1/device/control"
    sku, device = device_id.split("|")
    request_id = sku + datetime.now().strftime("%d%m%Y%H%M%S")
    if (action == "on"):
        govee_action = 1
    else:
        govee_action = 0
    payload = json.dumps({
        "requestId": request_id,
        "payload": {
            "sku": sku,
            "device": device,
            "capability": {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": govee_action
            }
        }
    })
    # print(payload)
    headers = {
        'Govee-API-Key': api_key,
        'Content-Type': 'application/json' 
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    
    return response_json

# Get token for use over SmartThings from Samsung
def get_tapo_token():
    # You will need a ifttt_token.json file in the root with these attributes:
    # {
    #     "url": "xxxxxxxx",
    #     "api_key": "xxxxxxx"
    # }

    # Get Tapo credentials
    filename = "tapo_token.json"
    with open(filename, "r") as f:
        data = json.load(f)
    api_key = data.get("api_key")
    url_base = data.get("url")

    return api_key, url_base

# Get state from one Tapo devices over Smarthings from Samsung
# For the moment only for switches
def get_tapo_device_state(device_list, url_base, api_key):
    url = url_base + "/v1/devices/"
    payload = {}
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    response_description = []
    # Get Tapo Status for each one
    for id in device_list:
        url = url_base + "/devices/" + id + "/status"
        # print(url)
        # print(headers)
        response = requests.request("GET", url, headers=headers, data=payload)
        # print(response)
        device_value = response.json()['components']['main']['switch']['switch']['value']
        if (device_value == "on"):
            switch_status = True
            switch_online = True
        elif (device_value == "off"):
            switch_status = False
            switch_online = True
        else:
            switch_status = False
            switch_online = False
        response_description.append(
                    {
                        "id": id,
                        "status": switch_status,
                        "type": "tapo",
                        "online": switch_online
                    }
                )

    return response_description

# Set action (on/off) for a Tapo devices over Smarthings from Samsung
def set_tapo_light_action(device_id, url_base, api_key, action):
    url = url_base + "/devices/" + device_id + "/commands"
    # print(url)
    payload = json.dumps({
        "commands": [
            {
            "component": "main",
            "capability": "switch",
            "command": action
            }
        ]
    })
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response

# Set action (on/off) for a Tapo devices over Smarthings from Samsung
def set_tapo_irrigation_action(device_id, url_base, api_key, action):
    url = url_base + "/devices/" + device_id + "/commands"
    # print(url)
    payload = json.dumps({
        "commands": [
            {
            "component": "main",
            "capability": "switch",
            "command": action
            }
        ]
    })
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response

# Get sensor devices list
def get_sensor_list():
    # You will need a sensor_list.json file with the list of sensors and these attributes:
    # {
    #     "sensors": [
    #         {
    #             "name": "sunrise",
    #             "type": "shelly",
    #             "id": "5432045e3fb8"
    #         }
    #     ]
    # }

    # Get sensor list
    filename = "sensor_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    sensors = data.get("sensors")
    # print(sensors)

    return sensors

# Get blind devices list
def get_blind_list():
    # You will need a blind_list.json file with the list of blinds and these attributes:
    # {
    #     "blinds": [
    #         {
    #             "name": "sunrise",
    #             "type": "shelly",
    #             "id": "5432045e3fb8"
    #         }
    #     ]
    # }

    # Get blind list
    filename = "blind_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    blinds = data.get("blinds")
    # print(blinds)

    return blinds

# Get light devices list
def get_light_list():
    # You will need a light_list.json file with the list of blinds and these attributes:
    # {
    #     "lights": [
    #         {
    #             "name": "comdedor",
    #             "type": "shelly",
    #             "id": "5432045e3fb8"
    #         }
    #     ]
    # }

    # Get light list
    filename = "light_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    lights = {}
    lights = data.get("lights")
    # print(lights)
    
    return lights

# Get light devices list
def get_irrigation_list():
    # You will need a light_list.json file with the list of blinds and these attributes:
    # {
    #     "irrigation": [
    #         {
    #             "name": "comdedor",
    #             "type": "shelly",
    #             "id": "5432045e3fb8"
    #         }
    #     ]
    # }

    # Get irrigation list
    filename = "irrigation_list.json"
    with open(filename, "r") as f:
        data = json.load(f)
    irrigation = {}
    irrigation = data.get("irrigation")
    # print(lights)
    
    return irrigation

# Decode user for basic auth
def decode_basic_auth(auth_header: str):
    # Ejemplo de header: "Basic YWRtaW46MTIzNA=="
    if not auth_header.startswith("Basic "):
        raise ValueError("No es un encabezado Basic Auth válido")
    
    # Extraer la parte codificada
    encoded_credentials = auth_header.split(" ")[1]

    # Decodificar base64 → bytes → string
    decoded_bytes = base64.b64decode(encoded_credentials)
    decoded_str = decoded_bytes.decode("utf-8")

    # Separar usuario y contraseña
    username, password = decoded_str.split(":", 1)
    return username, password