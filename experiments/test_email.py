import smtplib


def send_email(context):
    sender = "Private Person <from@example.com>"
    receiver = "A Test User <to@example.com>"

    message = f"""\
    Subject: Hi Mailtrap
    To: {receiver}
    From: {sender}

    {context}"""

    with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
        server.starttls()
        server.login("ff290726d93e40", "84886f85cd896b")
        server.sendmail(sender, receiver, message)

if __name__ == "__main__":
    send_email("Hi testing")