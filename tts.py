from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import asyncio
from pydub import AudioSegment, exceptions
from pydub.playback import play
import json 
import io 
import time

class TTS:
    def __init__(self):
        self._websocket_client = None
    
    async def listen(self):
        async with serve(self._websocket_handler, host='localhost', port = 9876) as server:
            await server.serve_forever()

    async def _websocket_handler(self, websocket):
        if self._websocket_client is None:
            print("Voice: New client connected")
            self._websocket_client = websocket
            await websocket.wait_closed()
            print("Voice: Client disconnected")
            self._websocket_client = None
        else:
            print("Voice: Client already connected, rejecting new connection")

    async def _recv_message(self):
        if self._websocket_client is None:
            raise Exception("Voice: No client connected")
        try:
            return await self._websocket_client.recv()
        except ConnectionClosed:
            print("Voice: Client is disconnected")
            self._websocket_client = None

    async def _send_message(self, message):

        if self._websocket_client is None:
            raise Exception("Voice: No client connected")
        try: 
            await self._websocket_client.send(message)
        except ConnectionClosed:
            print("Voice: Client is disconnected")
            self._websocket_client = None

    async def generate_tts(self, message):
        if self._websocket_client is None:
            raise Exception("Voice: No client connected")
        try:
            request = {"message": message.response_text}
            await self._send_message(json.dumps(request))
            audio_bytes = await self._recv_message()

            if audio_bytes is None:
                print("Voice: No audio segment received")
                return None
        except ConnectionClosed:
            print("Voice: Client is disconnected")
            self._websocket_client = None
        try: 
            return await asyncio.to_thread(AudioSegment.from_file, io.BytesIO(audio_bytes), format="wav")
        except exceptions.CouldntDecodeError:
            print("Voice: Failed to decode audio segment")
            return None

async def tts_loop(voice, tts_queue, speech_queue):
    while True:
        message = await tts_queue.get()
        try:
            start = time.time()
            res = await voice.generate_tts(message)
        except asyncio.CancelledError as e:
            raise e
        if res is not None:
            end = time.time()
            print(f"TTS Time: {end - start}s")
            message.audio_segment = res
            await speech_queue.put(message)
        else:
            print("TTS failed for message", message)
    # message -> chat_messages -> response from llm -> tts_queue -> voice websocket -> back here

async def speech_loop(speech_queue):
    while True:
        message = await speech_queue.get()
        print(f"Speech: {message.response_text}")
        if message.audio_segment is not None:
            play(message.audio_segment)
        else:
            print("Speech: No audio segment for message", message)