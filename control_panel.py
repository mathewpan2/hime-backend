from ws import WS
import json
from unity import Unity
import asyncio

class ControlPanel(WS):
    def __init__(self, host, port):
        super().__init__("Control Panel", host, port)
    
    async def send_message(self, message):
        res = await self._send_message(json.dumps(message.__dict__))
    
async def control_panel_loop(control_panel: ControlPanel, unity: Unity, talking_event: asyncio.Event):
    while True:
        request = await control_panel._recv_message()
        if request is not None:
            request = json.loads(request)
            if request["type"] == "cancelSpeechRequest":
                await unity.send_command(request["type"])

            if request["type"] == "stopSpeechRequest":
                talking_event.clear()
            if request["type"] == "startSpeechRequest":
                talking_event.set()
            print(f"Control Panel received message: {request}")



