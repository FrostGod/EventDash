import os
import requests
from typing import Optional


class MailgunEmailSender:
    def __init__(self, api_key: Optional[str] = None, domain_name: Optional[str] = None):
        self.api_key = os.getenv("MAILGUNAPIKEY")
        self.domain_name = "sandbox40e98b4320474ce4be2481e0cda373fd.mailgun.org"
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or through the MAILGUNAPIKEY environment variable.")
        print(f"API Key: {self.api_key}")
        print(f"Domain Name: {self.domain_name}")

    def send_email(self, email: str, subject: str = "Hello", text: str = "Testing some Mailgun awesomeness!") -> requests.Response:
        email = "divesh.chowdary@gmail.com"
        response = requests.post(
            f"https://api.mailgun.net/v3/{self.domain_name}/messages",
            auth=("api", self.api_key),
            data={
                "from": f"Excited User <mailgun@{self.domain_name}>",
                "to": [email],
                "subject": subject,
                "text": text
            }
        )
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        return response

# Example usage
# You can now initialize the MailgunEmailSender class and use it to send emails.
# email_sender = MailgunEmailSender()
# email_sender.send_email("recipient@example.com")
