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
        if self._websocket_client is None:
            raise Exception("LLM: No client connected")
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
                    emotion = await loop.run_in_executor(None, classifier.classify_emotion, response.response)
                    tts = HimeSpeechEvent(response.type, message.user_message, response.response, emotion)
                    tts_queue.put_nowait(tts)
                    response = await llm.receive_response()
                
                if response.type == "EndSpeech":
                    await tts_queue.put(HimeSpeechEvent(response.type, message.user_message, "", ""))
                    
                
            except asyncio.QueueFull:
                print("TTS Queue is full, dropping message: " + message.response_text)
        else:
            print("LLM failed for message: ", message)