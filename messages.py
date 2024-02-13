
from abc import ABC, abstractmethod
import discord
from discord.ext import tasks
from stt_client import TranscriptionClient
import asyncio

class Messages(ABC):
    def __init__(self, client, onmessage):
        self._client = client
        self.onmessage = onmessage
    
    @abstractmethod
    async def listen(self, message):
        pass

    @abstractmethod
    async def _onmessage(self, message_content, message_author):
        pass

class DiscrodSTT(Messages):
    def __init__(self, onmessage):
        self._client = None
        self.onmessage = onmessage
    async def listen(self):
        self._client = TranscriptionClient(
            "0.0.0.0",
            9090,
            lang="en",
            model="small",
            onmessage=self._onmessage,
        )
        self._client()
    async def _onmessage(self, message_content, message_author):
        self.onmessage(message_content, message_author)

        self._client()

class Discord(Messages):
    def __init__(self, client, onmessage, ttsqueue):
        self._client = client
        self.onmessage = onmessage
        self.ttsqueue = ttsqueue
    
    async def listen(self):
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents, ttsqueue=self.ttsqueue)

        @client.event
        async def on_ready():
            print(f'We have logged in as {client.user}')
            # client.loop.create_task(send_message_loop())
        
        @client.event
        async def on_message(message):
            if message.author == client.user or message.author.bot:
                return
            if message.channel.id == 983138529775341650: # test
                self._onmessage(message.content, message.author.name)
        
        async def send_message_loop():
            while not client.is_closed():
                message = await self.ttsqueue.get()
                print(message)
                await client.get_channel(983138529775341650).send(message.response_text)

        
        
        await client.start(self._client, reconnect=True)

    def _onmessage(self, message_content, message_author):
        self.onmessage(message_content, message_author)

