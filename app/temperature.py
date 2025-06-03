######################################
## Get temperature, store it and
## retrieve for the app
######################################

from modules import insert_db, ifttt_app, get_db
import json
import os
from datetime import datetime, timedelta
import pytz
import requests

## Set temperature registers in dynamoDB
## Aqara registers will come in body 
def set_temperature(event, context):
    ## Get Event parameters
    print("Set Temperature Event -------------------------------------------")
    # print(event)
    body = json.loads(event["body"])
    print(body)

    ## Check if body has the attributes
    if ("sensor" in body.keys() and
        "temperature in body.keys()"):
        event = {
                    "sensor": body['sensor'],
                    "temperature": body['temperature']
                }
        ttl_days = int(os.environ['RETENTION_DAYS'])
        temperature_table = os.environ['AWS_DYNAMO_TEMP_TABLE']
        status_code, response = insert_db(
            table_name = temperature_table, 
            event_parameters = event, 
            ttl_days = ttl_days
        )
        status = 200
        response_description = 'Registro de temperatura insertado'
    else:
        status = 400
        response_description = 'Petición mal formada'

    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_description
    }

## Set temperature registers in dynamoDB
## Netatmo registers will be askwd for 
def fix_temperature(event, context):
    ## Get Event parameters
    print("Set Temperature Event -------------------------------------------")
    # print(event)
    # body = json.loads(event["body"])
    # print(body)

    ## Check for temperature data with Netatmo
    # TODO llevar esto a secrets
    CLIENT_ID = '68341a0e7c35e6ca44045c72'
    CLIENT_SECRET = 'IMhyhffoWqEKBHjVSR5LWjG6STXev4'
    REFRESH_TOKEN = '567dc11465d1c4628ec91df2|7b236a795456f7f3f2aad241dcd55587'

    # Get new acces_token
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
        for register in module_data:
            # Translate sensor name
            if (register['sensor'] == "Lledoner (Comedor)"): sensor = "comedor"
            elif (register['sensor'] == "Balcón"): sensor = "balcon"
            elif (register['sensor'] == "Habitación"): sensor = "habitacion"
            else: sensor = "otro"
            event = {
                    "sensor": sensor,
                    "temperature": register['temperature']
                }
            ttl_days = int(os.environ['RETENTION_DAYS'])
            temperature_table = os.environ['AWS_DYNAMO_TEMP_TABLE']
            status_code, response = insert_db(
                table_name = temperature_table, 
                event_parameters = event, 
                ttl_days = ttl_days
            )
            status = 200
            response_description = 'Registro de temperatura insertado'

    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_description
    }

def get_temperature(event, context):
    ## Get Event parameters
    print("Set Temperature Event -------------------------------------------")
    # print(event)
    # body = json.loads(event["body"])
    # print(body)

    # Get all data from the table
    temperature_table = os.environ['AWS_DYNAMO_TEMP_TABLE']
    data = get_db(temperature_table)
    data_fix = []
    for register in data:
        data_fix.append(
            {
                "sensor": register['sensor'],
                "event_date": register['event_date'],
                "temperature": register['temperature']
            }
        )


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
        },
        "body": json.dumps(data_fix)
    }