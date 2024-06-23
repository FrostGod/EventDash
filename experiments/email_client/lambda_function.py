import boto3
import json

def lambda_handler(event, context):
    # Initialize the SES client
    ses_client = boto3.client('ses')
    
    # Extract the message, subject, sender, and recipient from the event
    message = event['message']
    subject = event['subject']
    sender = event['sender']
    recipient = event['recipient']
    
    response = ses_client.send_email(
        Source=sender,
        Destination={
            'ToAddresses': [
                recipient,
            ]
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': message
                }
            }
        }
    )
    
    # Return a success message
    return {
        'statusCode': 200,
        'body': json.dumps('Email sent successfully')
    }


import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
