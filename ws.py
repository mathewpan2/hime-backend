from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import time
import json
from asyncio import Event

class WS:
    def __init__(self, name, host, port):
        self._websocket_client = None
        self.port = port
        self.name = name
        self.host = host
        self.awake_event = Event()

    async def listen(self): # called to start the server
        async with serve(self._websocket_handler, host=self.host, port = self.port) as server:  # creates the llm server 
            await server.serve_forever()
    
    async def _websocket_handler(self, websocket):
        if self._websocket_client is None:
            print(f"{self.name}: New client connected")
            self._websocket_client = websocket
            self.awake_event.set()
            await websocket.wait_closed()
            print(f"{self.name}: Client disconnected")
            self._websocket_client = None
            self.awake_event.clear()
        else:
            print(f"{self.name}: Client already connected, rejecting new connection")

    async def _recv_message(self):
        await self.awake_event.wait()
        if self._websocket_client is None:
            raise Exception(f"{self.name}: No client connected")
        try:
            return await self._websocket_client.recv()
        except ConnectionClosed:
            print(f"{self.name}: Client is disconnected")
            self._websocket_client = None

    async def _send_message(self, message):
        await self.awake_event.wait()
        if self._websocket_client is None:
            raise Exception(f"{self.name}: No client connected")
        try: 
            await self._websocket_client.send(message)
        except ConnectionClosed:
            print(f"{self.name}: Client is disconnected")
            self._websocket_client = None
    

