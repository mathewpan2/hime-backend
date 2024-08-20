from ws import WS
from dataclass import UnitySpeechEvent, getCurrentResponse
import asyncio
import msgpack
import time
import json
# this should send a completed speech event to the Unity Backend

class Unity(WS):
    def __init__(self, host, port):
        super().__init__("Unity", host, port)
    async def send_speech(self, speech: UnitySpeechEvent):
        pack = msgpack.packb(speech.__dict__)
        start = time.time()
        await self._send_message(pack)
        end = time.time()
        print(f"Unity: Speech finished for: {speech.response} in {end - start}s")
    
    async def send_command(self, command):
        req : UnitySpeechEvent = UnitySpeechEvent(type=command)
        pack = msgpack.packb(req.__dict__)
        await self._send_message(pack)

async def unity_loop(unity: Unity, control_panel, speech_queue, not_speaking_event: asyncio.Event):
    while True:
        speech : UnitySpeechEvent = await speech_queue.get()
        try:
            not_speaking_event.clear()
            payload = getCurrentResponse(speech.type, speech.response)
            await control_panel.send_message(payload)
            res = await unity.send_speech(speech)
            print(res)
        except asyncio.CancelledError as e:
            raise e

async def unity_listen_loop(unity: Unity, not_speaking_event: asyncio.Event):
    while True:
        try:
            request = await unity._recv_message()
            if request is not None:
                request = json.loads(request)
                if request["type"] == "EndSpeech":
                    print("Unity: EndSpeech received")
                    not_speaking_event.set()
        except asyncio.CancelledError as e:
            raise e