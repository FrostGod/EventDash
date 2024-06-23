import json
from random_number import RandomNumberGenerator
from services import Services


def lambda_handler(event, context):
    print(event)

    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = {param['name']: param['value']
                  for param in event['parameters']}

    responseBody = {
        "TEXT": {
            "body": json.dumps(handle_request(function, parameters))
        }
    }
    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': responseBody
        }
    }

    function_response = {'response': action_response,
                         'messageVersion': event['messageVersion']}
    print("Response: {}".format(function_response))

    return function_response


def handle_request(function, parameters):
    if function == "getRandomNumber":
        return RandomNumberGenerator.get_random_number(parameters.get('username'))
    if function == "getServices":
        return Services.get_services(parameters.get('service_type', 'city'))
    else:
        return {"error": "Invalid API path"}
