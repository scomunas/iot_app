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
def get_shelly_device_state(device_id, url_base, api_key):
    url = url_base + "/device/status"
    payload = 'auth_key=' + api_key + '&id=' + device_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    # print(response_json)
    
    return response_json

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
    url = url_base + "/device/relay/roller/control"
    # print(url)
    payload = 'auth_key=' + api_key + '&id=' + device_id + '&direction=' + action
    # print(payload)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    
    return response_json

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