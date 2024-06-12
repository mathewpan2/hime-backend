# this is the main server that runs all the server websockets and is resonsible for 
# managing all parts of the application


# you need client classes 

import asyncio 
import time
import signal
import sys
import asyncio
from asyncio.queues import Queue, PriorityQueue
from llm import LLM, llm_loop, EmotionsClassifier
from messages import Twitch
from dotenv import load_dotenv
from dataclass import ChatSpeechEvent, UnitySpeechEvent
from azure_tts import TTS, tts_loop
from unity import Unity, unity_loop
from control_panel import  ControlPanel, control_panel_loop
message_queue = PriorityQueue(maxsize=10)
tts_queue = Queue(maxsize=10)
speech_queue = Queue(maxsize=10)
load_dotenv()


def add_message(message: str, user: str):
    speech_event = ChatSpeechEvent(message, user)
    try: 
        message_queue.put_nowait(speech_event)
        print(f"Chat message added to queue ({user}|{speech_event.priority}): {message}")
    except asyncio.QueueFull:
        # ignore message since queue is full 
        print("Chat message queue is full, message dropped")

async def main():
    llm = LLM("0.0.0.0", 9877)
    unity = Unity("0.0.0.0", 9878)
    control = ControlPanel("0.0.0.0", 9879)
    tts = TTS()
    classifier = EmotionsClassifier()
    messages = Twitch(onmessage=add_message)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(llm.listen())
        tg.create_task(unity.listen())
        tg.create_task(messages.listen())
        tg.create_task(control.listen())
        tg.create_task(control_panel_loop(control))
        tg.create_task(unity_loop(unity, control, speech_queue))
        tg.create_task(llm_loop(llm, classifier, message_queue, tts_queue))
        tg.create_task(tts_loop(tts, tts_queue, speech_queue))
        # tg.create_task(speech_loop(speech_queue, tts))
        print(f"started at {time.strftime('%X')}")


    
if __name__ == '__main__':
    # with open("tts.ogg", "rb") as f:
    #     audio = f.read()
    # print(len(audio))
    # speech_queue.put_nowait(UnitySpeechEvent("NewSpeech", "Hello, world!", "Hello, world!", "default", audio))
    loop = asyncio.get_event_loop()
    # loop.add_signal_handler(signal.SIGINT, sys.exit) # TODO: clean shutdown
    loop.create_task(main())
    try:
        loop.run_forever()
    finally:
        loop.close()
