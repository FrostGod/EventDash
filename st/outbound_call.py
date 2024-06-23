import time
import redis
from typing import Optional
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import (
    RedisConfigManager,
)
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
import logging
import asyncio
import os
from langchain.agents import tool
from dotenv import load_dotenv

from vocode.streaming.models.message import BaseMessage
from call_transcript_utils import delete_transcript

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


def get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        if 'There is no current event loop in thread' in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            raise
    return loop


async def get_transcript(conversation_id: str, pubsub) -> Optional[str]:
    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            return message['data']
        await asyncio.sleep(1)  # Non-blocking sleep


@tool("call phone number")
def call_phone_number(input: str) -> str:
    """calls a phone number as a bot and returns a transcript of the conversation.
    the input to this tool is a pipe separated list of a phone number, a prompt, and the first thing the bot should say.
    The prompt should instruct the bot with what to do on the call and be in the 3rd person,
    like 'the assistant is performing this task' instead of 'perform this task'.

    should only use this tool once it has found an adequate phone number to call.

    for example, `+15555555555|the assistant is explaining the meaning of life|i'm going to tell you the meaning of life` will call +15555555555, say 'i'm going to tell you the meaning of life', and instruct the assistant to tell the human what the meaning of life is.
    """
    phone_number, prompt, initial_message = input.split("|", 2)
    call = OutboundCall(
        base_url=os.environ["TELEPHONY_SERVER_BASE_URL"],
        to_phone=phone_number,
        from_phone=os.environ["OUTBOUND_CALLER_NUMBER"],
        config_manager=RedisConfigManager(),
        agent_config=ChatGPTAgentConfig(
            prompt_preamble=prompt,
            initial_message=BaseMessage(text=initial_message),
        ),
        telephony_config=TwilioConfig(
            account_sid=os.environ["TWILIO_ACCOUNT_SID"], auth_token=os.environ["TWILIO_AUTH_TOKEN"]
        ),
    )

    loop = get_or_create_event_loop()

    async def manage_call():
        await call.start()
        redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        pubsub = redis_client.pubsub()
        pubsub.subscribe(call.conversation_id)

        try:
            transcript = await get_transcript(call.conversation_id, pubsub)
            delete_transcript(call.conversation_id)
            return transcript
        finally:
            pubsub.unsubscribe(call.conversation_id)
            redis_client.close()
            await call.end()

    return loop.run_until_complete(manage_call())
