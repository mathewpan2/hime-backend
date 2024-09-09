# this is the main server that runs all the server websockets and is resonsible for 
# managing all parts of the application


# you need client classes 
import asyncio 
import time
import signal
import sys
import asyncio
from asyncio.queues import Queue, PriorityQueue
from llm import LLM, llm_loop, EmotionsClassifier, PromptLLM, prompt_gen_loop
from messages import Twitch
from dotenv import load_dotenv
from dataclass import ChatSpeechEvent, UnitySpeechEvent
from azure_tts import TTS, tts_loop
from unity import Unity, unity_loop, unity_listen_loop
from control_panel import  ControlPanel, control_panel_loop
from llama_cpp import Llama
from dataclass import parameters
from osu import Osu, osu_listen_loop
from profanity_filter import ProfanityFilter

# Queues

chat_queue = PriorityQueue(maxsize=3)
message_queue = PriorityQueue(maxsize=10)
tts_queue = Queue(maxsize=10)
speech_queue = Queue(maxsize=10)


# Events

prompt_gen_event = asyncio.Event()
not_speaking_event = asyncio.Event()
talking_event = asyncio.Event()



def message_queue_empty():
    return message_queue.empty() and tts_queue.empty() and speech_queue.empty()


last_speech = time.time()

load_dotenv()



def add_chat_message(message: str, user: str):
    speech_event = ChatSpeechEvent(message, user)
    try: 
        chat_queue.put_nowait(speech_event)
    except asyncio.QueueFull:
        # ignore message since queue is full 
        print("Chat message queue is full, message dropped")


def add_message(message: str, user: str, platform:str = ''):
    speech_event = ChatSpeechEvent(message, user, platform)
    try: 
        message_queue.put_nowait(speech_event)
        print(f"Chat message added to queue ({user}|{speech_event.priority}): {message}")
        message_in_queue_flag = True
    except asyncio.QueueFull:
        # ignore message since queue is full 
        print("Chat message queue is full, message dropped")

async def main():
    llm = LLM("0.0.0.0", 9877)
    unity = Unity("0.0.0.0", 9878)
    control = ControlPanel("0.0.0.0", 9879)
    tts = TTS()
    osu = Osu("0.0.0.0", 9880)
    classifier = EmotionsClassifier()
    messages = Twitch(onmessage=add_chat_message)
    prompt = PromptLLM(add_message)
    filter = ProfanityFilter()
    not_speaking_event.set()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(llm.listen())
        tg.create_task(unity.listen())
        tg.create_task(messages.listen())
        tg.create_task(control.listen())
        tg.create_task(osu.listen())
        tg.create_task(control_panel_loop(control, unity, talking_event))
        tg.create_task(unity_loop(unity, control, speech_queue, not_speaking_event))
        tg.create_task(unity_listen_loop(unity, not_speaking_event))
        tg.create_task(llm_loop(llm, filter, classifier, message_queue, tts_queue))
        tg.create_task(tts_loop(tts, tts_queue, speech_queue))
        tg.create_task(prompt_gen_loop(prompt, filter, chat_queue , not_speaking_event, talking_event, message_queue_empty))
        tg.create_task(osu_listen_loop(osu, talking_event))
        # tg.create_task(speech_loop(speech_queue, tts))
        print(f"started at {time.strftime('%X')}")


    
if __name__ == '__main__':
    # with open("tts.ogg", "rb") as f:
    #     audio = f.read()
    # print(len(audio))
    # speech_queue.put_nowait(UnitySpeechEvent("NewSpeech", "Hello, world!", "default", audio))
    # prompt = PromptLLM(add_message, prompt_gen_event)
    # prompt_thread = Thread(target=prompt.run)
    loop = asyncio.get_event_loop()
    # loop.add_signal_handler(signal.SIGINT, sys.exit) # TODO: clean shutdown
    loop.create_task(main())
    # prompt_thread.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.stop()
    finally:
        # prompt.stop()
        # prompt_thread.join()
        loop.close()
        
