from azure_tts import TTS
from dotenv import load_dotenv
import asyncio
load_dotenv()
tts = TTS()

async def main():
    print(await tts.generate_tts("Hello, world!", "default"))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()