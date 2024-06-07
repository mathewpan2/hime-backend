from ws import WS
import json

class ControlPanel(WS):
    def __init__(self, host, port):
        super().__init__("Control Panel", host, port)
    
    async def send_message(self, message):
        res = await self._send_message(json.dumps(message.__dict__))
    
async def control_panel_recv_loop(control_panel: ControlPanel):
    while True:
        await control_panel.awake_event.wait()
        request = await control_panel._recv_message()
        if request is not None:
            request = json.loads(request)
            print(f"Control Panel received message: {request}")



