import json
import os
from slack_sdk import WebClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
client = WebClient(token=BOT_TOKEN)


def lambda_handler(event, context):
    slack_event = json.loads(event['body'])

    if slack_event.get("type") == "url_verification":
        return {"statusCode": 200, "body": slack_event.get("challenge")}

    elif slack_event.get("event"):
        data = slack_event.get("event")
        event_type = data.get("type")

        if event_type == "app_mention":
            channel_id = data.get("channel")
            client.chat_postMessage(
                channel=channel_id, text="👋 Hello there! I'm Serverless Slack App, here to make your day a little easier. 😊")
        return
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "hello world",
                }
            ),
        }
