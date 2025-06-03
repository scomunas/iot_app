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

# Check if some registers exists in table
def check_db(table_name, type, date, id, state):
    dynamodb = boto3.client('dynamodb')

    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression='event_type = :event_type AND event_date >= :event_date',
        ExpressionAttributeValues={
            ':event_type': {'S': type},
            ':event_date': {'S': date}
        },
        ScanIndexForward=False
    )
    # print(response)
    
    event_number = 0
    
    for item in response['Items']:
        event_id = item['event_id']['S']
        event_state = item['event_state']['S']
        if ((event_id == id or id == 'any') and
            (event_state == state or state == 'any')):
            event_number += 1

    return event_number, response['Items']

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

# Get sunrise/sunset from https://sunrisesunset.io/api/
def get_sunrise(lat, long):
    url = "https://api.sunrisesunset.io/json?lat=" + \
        str(lat) + \
        "&lng=" + \
        str(long)

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code >= 200 and response.status_code < 300:
        response_json = json.loads(response.text)
        sunrise = datetime.strptime(response_json['results']['sunrise'], "%I:%M:%S %p")
        sunset = datetime.strptime(response_json['results']['sunset'], "%I:%M:%S %p")
        data = {
            "status": 200,
            "results": {
                "sunrise": sunrise,
                "sunset": sunset    
            }
        }
    else:
        data = {
            "status": 400,
            "results": {
            }
        }
    
    return data

# Get holiday list from https://date.nager.at/api
def get_holidays(country, county):
    year = datetime.now().year
    url = "https://date.nager.at/api/v3/publicholidays/" + \
        str(year) + \
        "/" + \
        str(country)

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code >= 200 and response.status_code < 300:
        response_json = json.loads(response.text)
        holiday_list = []
        for holiday in response_json:
            if (holiday['global'] == True or
                county in holiday['counties']):
                holiday_list.append(holiday['date'])
        data = {
            "status": 200,
            "results": holiday_list  
        }
    else:
        data = {
            "status": 400,
            "results": {
            }
        }
    
    return data
    
# Store config file
def put_config_file(data):
    bucket = os.environ['S3_BUCKET']
    s3 = boto3.resource('s3')
    s3object = s3.Object(bucket, 'config.json')
    response = s3object.put(
        Body=(bytes(json.dumps(data).encode('UTF-8')))
    )
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    # Return status value
    return status_code, response['ResponseMetadata']

# Retrieve config file
def get_config_file():
    bucket = os.environ['S3_BUCKET']
    s3 = boto3.resource('s3')
    s3object = s3.Object(bucket, 'config.json')
    file_content = s3object.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    return json_content

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

# Create event in eventbridge scheduler
def event_create(name, event, target_lambda, schedule, event_group):
    scheduler = boto3.client('scheduler')

    flex_window = { "Mode": "OFF" }

    eventbridge_target = {
        "RoleArn": os.environ['EVENTBRIDGE_ROLE'],
        "Arn": target_lambda,
        "Input": json.dumps(event),
        'RetryPolicy': {
                'MaximumEventAgeInSeconds': 3600,
                'MaximumRetryAttempts': 0
            },
    }

    scheduler.create_schedule(
        Name = name,
        ActionAfterCompletion='DELETE',
        ScheduleExpression = 'at(' + schedule + ')',
        ScheduleExpressionTimezone = 'CET',
        State='ENABLED',
        GroupName=event_group,
        Target=eventbridge_target,
        FlexibleTimeWindow=flex_window)

# Check schedule for concrete events
def event_check(group, rule):
    scheduler = boto3.client('scheduler')

    response = scheduler.list_schedules(
        GroupName=group,
        NamePrefix=rule,
        MaxResults=50
    )

    if (response['ResponseMetadata']['HTTPStatusCode'] == 200 and
        len(response['Schedules']) > 0):
        rule_found = True
    else:
        rule_found = False

    return rule_found

# Delete events for a group and name_prefix
def event_delete(group, name_prefix):
    scheduler = boto3.client('scheduler')

    response = scheduler.list_schedules(
        GroupName=group,
        NamePrefix=name_prefix,
        MaxResults=50
    )

    if (response['ResponseMetadata']['HTTPStatusCode'] == 200 and
        len(response['Schedules']) > 0):
        rule_found = True
    else:
        rule_found = False

    rule_deleted = True
    for schedule in response['Schedules']:
        scheduler.delete_schedule(
            GroupName=group,
            Name=schedule['Name']
        )

        if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
            rule_deleted = rule_deleted & True
        else:
            rule_deleted = False

    return rule_found & rule_deleted
