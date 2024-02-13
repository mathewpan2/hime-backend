from stt_client import TranscriptionClient
import torch


client = TranscriptionClient(
            "localhost",
            9090,
            lang="en",
            model="small",
        )
client()