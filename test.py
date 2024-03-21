from tts import TTS, play_audio
import asyncio
from dotenv import load_dotenv
load_dotenv()
tts = TTS()

async def main():
    result = await tts.generate_tts("I will kill you all.")
    play_audio(result)


if __name__ == "__main__":
    asyncio.run(main()) 