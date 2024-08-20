from typing import Any
from ws import WS
from asyncio import Event
import json

class Osu(WS):
    def __init__(self, host, port):
        super().__init__("Osu", host, port)



async def osu_listen_loop(osu: Osu, talking_event: Event):
    while True:
        request = await osu._recv_message()
        if request is not None:
            request = json.loads(request)
            if request["type"] == "stopSpeechRequest":
                talking_event.clear()
            if request["type"] == "startSpeechRequest":
                talking_event.set()
            print(f"Osu received message: {request}")
        else:
            print("Osu: Received empty message")
