import redis
import os
import time
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


def main(conversation_id):
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(conversation_id)

    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                print(message['data'])
            time.sleep(1)
    finally:
        pubsub.unsubscribe(conversation_id)
        redis_client.close()


if __name__ == "__main__":
    import sys
    conversation_id = sys.argv[1]
    main(conversation_id)
