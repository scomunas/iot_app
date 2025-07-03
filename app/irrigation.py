######################################
## Irrigation
## 
######################################

from modules import get_irrigation_list, get_tapo_token, set_tapo_irrigation_action
import json

## Set irrigation action
def set_irrigation_action(event, context):
    ## Get Event parameters
    print("|-0-| Set irrigation Action")
    body = json.loads(event["body"])
    print(f"|-0-| Body: {body}")

   ## Check if body has the attributes
    if ("irrigation" in body.keys()):
        if ("action" in body.keys()):
            print("|-0-| Irrigation action demanded")
            print("|-0-| Body check OK")

            # Get Irrigation list
            irrigations = get_irrigation_list()
            print(f"|-0-| Irrigation list obtained: {irrigations}")

            # Get Irrigation ID if there is in the list
            irrigation_id = 'none'
            for irrigation in irrigations:
                if (irrigation['name'] == body['irrigation']):
                    irrigation_id = irrigation['id']
                    irrigation_type = irrigation['type']

            if (irrigation_type == 'tapo'):
                print("|-0-| Tapo light")

                # Get token data
                api_key, url = get_tapo_token()
                print("|-0-| Token obtained")

                # Set shelly action
                response = set_tapo_irrigation_action(
                    device_id=irrigation_id,
                    url_base=url,
                    api_key=api_key,
                    action=body['action']
                )
                print(f"|-0-| Response for action: {response}")

                status = 200
                response_description = f"Irrigation {body['irrigation']} set for {body['action']}"
            else:
                print("|-0-| Irrigation not found")
                status = 400
                response_description = 'Irrigation not found'
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
