from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def send_sms(to: str, message: str):
    """
    Sends SMS to the given phone number using Twilio
    """
    if not to.startswith("+91"):
        to=f"+91{to}"

    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
    except Exception as e:
        print(f"Failed to send SMS to {to}: {e}")
