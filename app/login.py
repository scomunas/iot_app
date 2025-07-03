######################################
## Get login info
## 
######################################

from modules import decode_basic_auth
import json

## User Login
## TODO: Integrate with cognito
def login(event, context):
    ## Get Event parameters
    print("|-0-| Login")
    headers = event["multiValueHeaders"]
    print(f"|-0-| Headers: {headers}")

    # Get username and password
    user, password = decode_basic_auth(
        auth_header=headers['Authorization'][0]
    )
    print(f"|-0-| Usuario: {user}")
    print(f"|-0-| Password: {password}")

    # Authorization fixed
    # TODO integrate with cognito
    if ((user == "admin@casa.com") and
        (password == "z2-ddk.BRvxrroc2TVqF")):
        status = 200
        response_description = "User Accepted"
    else:
        status = 403
        response_description = "Unauthorized"

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
