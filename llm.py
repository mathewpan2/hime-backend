import asyncio 
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
from concurrent.futures import ProcessPoolExecutor
from dataclass import ChatSpeechEvent, HimeResponse, HimeSpeechEvent
import traceback
import time
import json
from ws import WS
import re
from transformers import pipeline
from asyncio.queues import Queue, PriorityQueue
from llama_cpp import Llama
from dataclass import parameters
import random
from openai import AsyncOpenAI
import os

class EmotionsClassifier():
    def __init__(self):
        self._model = pipeline("zero-shot-classification",model="facebook/bart-large-mnli", device=0)
        self._labels = ["angry", "cheerful", "excited", "sad", "shouting", "terrified", "unfriendly", "whispering"]

    def classify_emotion(self, response):
        result = self._model(response, self._labels)
        if result['scores'][0] > 0.45:
            emotion = result['labels'][0]
        else:
            emotion = "default"
        return emotion


        
class LLM(WS):
    def __init__(self, port, host):
        super().__init__("LLM", port, host)
    
    async def generate_response(self, prompt, person):
        # if self._websocket_client is None:
        #     raise Exception("LLM: No client connected")
        request = {"fName": "getHimeResponse", "message": prompt, "sysPromptSetting": "generic", "person": person}
        await self._send_message(json.dumps(request))

    async def receive_response(self):
        response = await self._recv_message()
        return HimeResponse(**json.loads(response))


async def llm_loop(llm: LLM, classifier: EmotionsClassifier, message_queue: PriorityQueue, tts_queue: Queue):
    while True:
        message: ChatSpeechEvent = await message_queue.get()
        try: 
            await llm.generate_response(message.user_message, message.user_name)
            response = await llm.receive_response()
        except asyncio.CancelledError as e:
            raise e
        except:
            print("Exception occured during LLM Fetch:")
            print(traceback.format_exc())
            response = None

        if response is not None:
            try:
                while response.type != "EndSpeech":
                    loop = asyncio.get_event_loop()
                    print(response.response)
                    # emotion = await loop.run_in_executor(None, classifier.classify_emotion, response.response)
                    emotion = "default"
                    tts = HimeSpeechEvent(response.type, message.user_message, response.response, emotion)
                    tts_queue.put_nowait(tts)
                    response = await llm.receive_response()
                
                if response.type == "EndSpeech":
                    await tts_queue.put(HimeSpeechEvent(response.type, message.user_message, "", ""))
                    
                
            except asyncio.QueueFull:
                print("TTS Queue is full, dropping message: " + message.response_text)
        else:
            print("LLM failed for message: ", message)



class PromptLLM():
    def __init__(self, add_message) -> None:
        self.add_message = add_message
        # self.llm: Llama = Llama(**parameters)
        self.llm = AsyncOpenAI(api_key=os.environ.get("OPENAI_KEY"))
        self.running = True
        with open(os.path.join("data", "prompt.txt")) as f:
            self.prompt = f.read()
        with open(os.path.join("data", "questions.txt")) as f:
            self.questions = f.readlines()
        # self.prompt = f"<start_of_turn>user\n{question}<end_of_turn>\n<start_of_turn>model\n"
        


    async def generate_prompt(self):
        # seed = time.time()
        # prompt = self.llm(self.prompt, max_tokens=50, seed=int(seed), stream=False)
        # return prompt['choices'][0]['text']
        questions = random.sample(self.questions, 3)
        prompt = self.prompt.replace("[dialogue1]", questions[0]).replace("[dialogue2]", questions[1]).replace("[dialogue3]", questions[2])
        res = await self.llm.chat.completions.create( 
            messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo"
        )

        return res.choices[0].message.content


async def prompt_gen_loop(prompt: PromptLLM, chat_queue: PriorityQueue, not_speaking_event: asyncio.Event, talking_event: asyncio.Event, message_queue_empty):
    while True:
        await talking_event.wait()
        await not_speaking_event.wait()
        await asyncio.sleep(3)
        if message_queue_empty() and not_speaking_event.is_set() and talking_event.is_set():
            # loop = asyncio.get_event_loop()
            # prompt_gen = await loop.run_in_executor(None, prompt.generate_prompt)
            if chat_queue.empty():
                prompt_gen = await prompt.generate_prompt()
                prompt.add_message(prompt_gen, "anon")
            else:
                chat: ChatSpeechEvent = chat_queue.get_nowait()
                prompt.add_message(chat.user_message, chat.user_name)