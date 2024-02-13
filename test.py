from stt_client import TranscriptionClient
import torch

tts_queue = ""
client = TranscriptionClient(
            "localhost",
            9090,
            lang="en",
            model="small",
            onmessage=tts_queue,
        )
client()