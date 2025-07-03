######################################
## Get temperature, store it and
## retrieve for the app
######################################

from modules import insert_db, get_db, get_netatmo_token, get_netatmo_data
import json
import os

## Set temperature registers in dynamoDB
## Aqara registers will come in body 
def set_temperature(event, context):
    ## Get Event parameters
    print("|-0-| Set Temperature")
    body = json.loads(event["body"])
    print(f"|-0-| Body: {body}")

    ## Check if body has the attributes
    if ("sensor" in body.keys() and
        "temperature" in body.keys()):
        print("|-0-| Body check OK")
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
        print("|-0-| Body check KO")
        status = 400
        response_description = 'Petición mal formada'

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

## Set temperature registers in dynamoDB
## Netatmo registers will be askwd for 
## No parameters because each time will
## write event for all sensors
def fix_temperature(event, context):


    ## Get Event parameters
    print("Set Temperature Event for Netatmo -------------------------------------------")

    ## Get Netatmo Token
    access_token = get_netatmo_token()
    print("|-0-| Token obtained")

    module_data = get_netatmo_data(access_token)
    print(f"|-0-| Netatmo info: {module_data}")

    # Get data from all the sensors
    
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

## Get temperature registers from dynamoDB
## no filter added, all registers will come 
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

    print(f"|-0-| Status: 200")
    print(f"|-0-| Reponse Description: {data_fix}")
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