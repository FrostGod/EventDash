from mailer import MailgunEmailSender
from langchain.tools import Tool

# Define the function that will be exposed as a tool


def send_mailgun_email(email: str, subject: str = "Inquiry", text: str = "Testing some Mailgun awesomeness!") -> str:
    email_sender = MailgunEmailSender()
    response = email_sender.send_email(email, subject, text)
    return response.text


# Create the LangChain Tool
send_mailgun_email_tool = Tool(
    name="send_mailgun_email",
    func=send_mailgun_email,
    description="Send an email using the Mailgun API. Requires recipient email address, subject, and text."
)
