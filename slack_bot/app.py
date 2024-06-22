import json
import os
import boto3
import uuid
import botocore

from slack_sdk import WebClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
client = WebClient(token=BOT_TOKEN)
BEDROCK_ID = os.environ.get('BEDROCK_ID')
BEDROCK_ALIAS = os.environ.get('BEDROCK_ALIAS')
bedrock_client = boto3.client('bedrock-agent-runtime')
br_config = botocore.config.Config(read_timeout=900,
                                   connect_timeout=900,
                                   retries={"max_attempts": 0})
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime", region_name="us-west-2", config=br_config)


def lambda_handler(event, context):
    slack_event = json.loads(event['body'])

    if slack_event.get("type") == "url_verification":
        return {"statusCode": 200, "body": slack_event.get("challenge")}

    elif slack_event.get("event"):
        data = slack_event.get("event")
        event_type = data.get("type")

        if event_type == "app_mention":
            channel_id = data.get("channel")
            text = data.get("text")
            user = data.get("user")

            session_id = str(uuid.uuid4())
            response = bedrock_agent_runtime.invoke_agent(
                agentId=BEDROCK_ID,      # Identifier for Agent
                agentAliasId=BEDROCK_ALIAS.split(
                    '|')[1],  # Identifier for Agent Alias
                sessionId=session_id,    # Identifier used for the current session
                inputText=f"{user}: {text}",  # Input
            )

            output = ""
            stream = response.get('completion')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        output += chunk.get('bytes').decode()

            client.chat_postMessage(
                channel=channel_id, text=output)

        return
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "ok",
                }
            ),
        }
