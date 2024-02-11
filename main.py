# this is the main server that runs all the server websockets and is resonsible for 
# managing all parts of the application


# you need client classes 

import asyncio 
import time
import signal
import sys
import asyncio
from asyncio.queues import Queue, PriorityQueue
from llm import LLM, llm_loop
from messages import Discord
from dotenv import load_dotenv
import os
from speechevent import ChatSpeechEvent

chat_messages = PriorityQueue(maxsize=3)
tts_queue = Queue(maxsize=2)
speech_queue = Queue(maxsize=2)
load_dotenv()


async def add_message(message: str, user: str):
    speech_event = ChatSpeechEvent(message, user)
    try: 
        chat_messages.put_nowait(speech_event)
        print(f"Chat message added to queue ({user}|{speech_event.priority}): {message}")
    except asyncio.QueueFull:
        # ignore message since queue is full 
        print("Chat message queue is full, message dropped")

async def main():
    llm = LLM()
    messages = Discord(os.environ['TOKEN'], add_message, tts_queue)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(llm.listen())
        tg.create_task(llm_loop(llm, chat_messages, tts_queue))
        tg.create_task(messages.connect())
        print(f"started at {time.strftime('%X')}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sys.exit) # TODO: clean shutdown
    loop.create_task(main())
    try:
        loop.run_forever()
    finally:
        loop.close()
