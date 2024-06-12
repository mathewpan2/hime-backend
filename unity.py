from ws import WS
from dataclass import UnitySpeechEvent, getCurrentResponse
import asyncio
from control_panel import ControlPanel
import msgpack
import time
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

async def unity_loop(unity: Unity, control: ControlPanel, speech_queue):
    while True:
        speech : UnitySpeechEvent = await speech_queue.get()
        try:
            payload = getCurrentResponse(speech.response)
            res = await control.send_message(payload)
            res = await unity.send_speech(speech)
            print(res)
        except asyncio.CancelledError as e:
            raise e
