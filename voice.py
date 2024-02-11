from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import asyncio
from pydub import AudioSegment

class Voice:
    def __init__(self):
        self._websocket_client = None
        self.ready_for_speech = False
        self.tts_paused = False
    
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
            await self._send_message(message.response_text)
            audio_segment = await self._recv_message()
            return await asyncio.to_thread(AudioSegment.from_file, audio_segment)

        except ConnectionClosed:
            print("Voice: Client is disconnected")
            self._websocket_client = None

async def tts_loop(voice, tts_queue, speech_queue):
    pass
    
    # message -> chat_messages -> response from llm -> tts_queue -> voice websocket -> back here