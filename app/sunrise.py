######################################
## Get blind state and action it
## 
######################################

from modules import get_shelly_token, get_sensor_list, get_shelly_device_state

## Get sunrise state
## from shelly
def get_sunrise(event, context):
    ## Get Event parameters
    print("|-0-| Get Sunrise")

    # Get Shelly token
    api_key, url = get_shelly_token()
    print("|-0-| Shelly token obtained")
    
    # Get sensor list
    sensors = get_sensor_list()
    print(f"|-0-| Sensor list obtained: {sensors}")

    ## Look for sunrise sensor
    sensor_id = ""
    for sensor in sensors:
        if (sensor['name'] == "sunrise"):
            sensor_id = sensor['id']
            # print(sensor_id)

    if (sensor_id == ""):
        print("|-0-| Sunrise sensor not found")
        status = 400
        response_description = "Sensor not found"
    else:
        print(f"|-0-| Sunrise sensor found with id {sensor_id}")
        # Get device information
        shelly_status = get_shelly_device_state(
            device_list=[sensor_id],
            url_base=url,
            api_key=api_key
        )
        print(f"|-0-| Device status: {shelly_status}")

        # Check for status
        if (shelly_status[0]['online'] == 1):
            if (shelly_status[0]['status'] == True):
                status = 200
                response_description = "night"
            else:
                status = 200
                response_description = "day"
        else:
            status = 400
            response_description = "Device offline"

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
