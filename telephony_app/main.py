# Standard library imports
import os
import sys
import typing
import redis

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI
from loguru import logger
from pyngrok import ngrok

# Local application/library specific imports
from speller_agent import SpellerAgentFactory

from vocode.logging import configure_pretty_logging
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.telephony.server.base import TelephonyServer, TwilioInboundCallConfig
from vocode.streaming.utils import events_manager
from vocode.streaming.models.events import Event, EventType
from vocode.streaming.models.transcript import TranscriptCompleteEvent

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
load_dotenv()

configure_pretty_logging()

app = FastAPI(docs_url=None)

config_manager = RedisConfigManager()

BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth is not None:
        ngrok.set_auth_token(ngrok_auth)
    port = sys.argv[sys.argv.index(
        "--port") + 1] if "--port" in sys.argv else 3000

    # Open a ngrok tunnel to the dev server
    BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
    logger.info(
        'ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError(
        "BASE_URL must be set in environment if not using pyngrok")


CALL_TRANSCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__), "call_transcripts")


def add_transcript(conversation_id: str, transcript: str) -> None:
    redis_client = redis.Redis(host="redis", port=6379, db=0)
    redis_client.publish(conversation_id, transcript)
    redis_client.close()


class EventsManager(events_manager.EventsManager):
    def __init__(self):
        super().__init__([EventType.TRANSCRIPT_COMPLETE])

    async def handle_event(self, event: Event):
        if isinstance(event, TranscriptCompleteEvent):
            transcript_complete_event = typing.cast(
                TranscriptCompleteEvent, event)
            add_transcript(
                transcript_complete_event.conversation_id,
                transcript_complete_event.transcript.to_string(),
            )

        # print(f"got event: {event}")
        # if event.type == EventType.TRANSCRIPT_COMPLETE:
        #    transcript_complete_event = typing.cast(
        #        TranscriptCompleteEvent, event)
        #    add_transcript(
        #        transcript_complete_event.conversation_id,
        #        transcript_complete_event.transcript.to_string(),
        #    )


telephony_server = TelephonyServer(
    events_manager=EventsManager(),
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=ChatGPTAgentConfig(
                initial_message=BaseMessage(text="What up"),
                prompt_preamble="Have a pleasant conversation about life",
                generate_responses=True,
            ),
            # uncomment this to use the speller agent instead
            # agent_config=SpellerAgentConfig(
            #     initial_message=BaseMessage(
            #         text="im a speller agent, say something to me and ill spell it out for you"
            #     ),
            #     generate_responses=False,
            # ),
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
        )
    ],
    agent_factory=SpellerAgentFactory(),
)

app.include_router(telephony_server.get_router())
