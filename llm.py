import asyncio 
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
from dataclass import ChatSpeechEvent
import traceback
import time
import json
from ws import WS
import re
from transformers import pipeline
# class LLM:
#     def __init__(self):
#         self._websocket_client = None
    
#     async def listen(self): # called to start the server
#         async with serve(self._websocket_handler, host='0.0.0.0', port = 9877) as server:  # creates the llm server 
#             await server.serve_forever()
    
#     async def _websocket_handler(self, websocket):
#         if self._websocket_client is None:
#             print("LLM: New client connected")
#             self._websocket_client = websocket
#             await websocket.wait_closed()
#             print("LLM: Client disconnected")
#             self._websocket_client = None
#         else:
#             print("LLM: Client already connected, rejecting new connection")

#     async def _recv_message(self):
#         if self._websocket_client is None:
#             raise Exception("LLM: No client connected")
#         try:
#             return await self._websocket_client.recv()
#         except ConnectionClosed:
#             print("LLM: Client is disconnected")
#             self._websocket_client = None

#     async def _send_message(self, message):

#         if self._websocket_client is None:
#             raise Exception("LLM: No client connected")
#         try: 
#             await self._websocket_client.send(message)
#         except ConnectionClosed:
#             print("LLM: Client is disconnected")
#             self._websocket_client = None
    
    # async def generate_response(self, prompt, person):
    #     start = time.time()
    #     if self._websocket_client is None:
    #         raise Exception("LLM: No client connected")
    #     request = {"fName": "getHimeResponse", "message": prompt, "sysPromptSetting": "generic", "person": person}
    #     await self._send_message(json.dumps(request))
    #     llm_response_text = await self._recv_message()
    #     end = time.time()
    #     print(f"LLM Response Time: {end - start}s")
    #     return json.loads(llm_response_text)["llmResponse"]

class EmotionsClassifier():
    def __init__(self):
        self._model = pipeline("zero-shot-classification",model="facebook/bart-large-mnli", device=0)
        self._labels = ["angry", "cheerful", "excited", "sad", "shouting", "terrified", "unfriendly", "whispering"]

    def classify_emotion(self, responses):
        emotions = []
        for response in responses:
            result = self._model(response, self._labels)
            if result['scores'][0] > 0.45:
                emotions.append(result['labels'][0])
            else:
                emotions.append("default")
        return emotions


        


class LLM(WS):
    def __init__(self, port, host):
        super().__init__("LLM", port, host)
    
    async def generate_response(self, prompt, person):
        start = time.time()
        if self._websocket_client is None:
            raise Exception("LLM: No client connected")
        request = {"fName": "getHimeResponse", "message": prompt, "sysPromptSetting": "generic", "person": person}
        await self._send_message(json.dumps(request))
        llm_response_text = await self._recv_message()
        end = time.time()
        print(f"LLM Response Time: {end - start}s")
        return json.loads(llm_response_text)["llmResponse"]



async def llm_loop(llm: LLM, classifier: EmotionsClassifier, message_queue, tts_queue):
    while True:
        message: ChatSpeechEvent = await message_queue.get()
        try: 
            response = await llm.generate_response(message.user_message, message.user_name)
        except asyncio.CancelledError as e:
            raise e
        except:
            print("Exception occured during LLM Fetch:")
            print(traceback.format_exc())
            response = None
        
        if response is not None:
            try:
                # we need to split the response by punctuation
                split = re.findall(r'[^.!?]*[.!?]', response)
                if split:
                    message.response_text = split
                else:
                    message.response_text = [response]
                loop = asyncio.get_event_loop()
                message.emotions = await loop.run_in_executor(None, classifier.classify_emotion, message.response_text)

                await tts_queue.put(message)
            except asyncio.QueueFull:
                print("TTS Queue is full, dropping message: " + message.response_text)
        else:
            print("LLM failed for message: ", message)