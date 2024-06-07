from ws import WS
from dataclass import UnitySpeechEvent, getCurrentResponse
import json
import asyncio
from control_panel import ControlPanel
# this should send a completed speech event to the Unity Backend

class Unity(WS):
    def __init__(self, host, port):
        super().__init__("Unity", host, port)

    async def send_speech(self, chat_speech: UnitySpeechEvent):
        await self._send_message(json.dumps(chat_speech.__dict__))
        print(f"Unity: Speech started for: {chat_speech.full_message}")
        res = await self._recv_message()

        

async def unity_loop(unity: Unity, control: ControlPanel, speech_queue):
    while True:
        speech : UnitySpeechEvent = await speech_queue.get()
        try:
            payload = getCurrentResponse(speech.full_message)
            print("payload: ", payload)
            res = await control.send_message(payload)
            res = await unity.send_speech(speech)
            print(res)
        except asyncio.CancelledError as e:
            raise e
