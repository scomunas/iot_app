######################################
## Get blind state and action it
## 
######################################

from modules import get_shelly_token, get_sensor_list, get_shelly_device_state

## Get sunrise state
## from shelly
def get_sunrise(event, context):
    ## Get Event parameters
    print("Get Sunrise -------------------------------------------")

    # Get Shelly token
    api_key, url = get_shelly_token()
    
    # Get sensor list
    sensors = get_sensor_list()

    ## Look for sunrise sensor
    sensor_id = ""
    for sensor in sensors:
        if (sensor['name'] == "sunrise"):
            print("Sunrise detector")
            sensor_id = sensor['id']
            # print(sensor_id)

    if (sensor_id == ""):
        print("Sensor not found")
        status = 400
        response_description = "Sensor not found"
    else:
        print("Sensor found with id " + sensor_id)
        # Get device information
        response = get_shelly_device_state(
            device_id=sensor_id,
            url_base=url,
            api_key=api_key
        )
        # Check for correct response
        if (response['isok'] == True and
            "data" in response.keys()):
            if(response['data']['online'] == True):
                input_data = response['data']['device_status']['input:0']
                status = 200
                if (input_data['state'] == True):
                    response_description = "night"
                else:
                    response_description = "day"
        else:
            print("Response from Shelly KO")
            status = 400
            response_description = "Response from Shelly KO"

    print("Status:")
    print(status)
    print("Reponse Description:")
    print(response_description)
    status = 200
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
        },
        "body": "day"
    }
