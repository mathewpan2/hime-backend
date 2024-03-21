import asyncio 
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import traceback
import time
import json

class LLM:
    def __init__(self):
        self._websocket_client = None
    
    async def listen(self): # called to start the server
        async with serve(self._websocket_handler, host='0.0.0.0', port = 9877) as server:  # creates the llm server 
            await server.serve_forever()
    
    async def _websocket_handler(self, websocket):
        if self._websocket_client is None:
            print("LLM: New client connected")
            self._websocket_client = websocket
            await websocket.wait_closed()
            print("LLM: Client disconnected")
            self._websocket_client = None
        else:
            print("LLM: Client already connected, rejecting new connection")

    async def _recv_message(self):
        if self._websocket_client is None:
            raise Exception("LLM: No client connected")
        try:
            return await self._websocket_client.recv()
        except ConnectionClosed:
            print("LLM: Client is disconnected")
            self._websocket_client = None

    async def _send_message(self, message):

        if self._websocket_client is None:
            raise Exception("LLM: No client connected")
        try: 
            await self._websocket_client.send(message)
        except ConnectionClosed:
            print("LLM: Client is disconnected")
            self._websocket_client = None
    
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


async def llm_loop(llm, chat_messages, tts_queue):
    while True:
        message = await chat_messages.get()
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
                message.response_text = response
                await tts_queue.put(message)
            except asyncio.QueueFull:
                print("TTS Queue is full, dropping message: " + message.response_text)
        else:
            print("LLM failed for message: ", message)