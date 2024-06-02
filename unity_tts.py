from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import asyncio
from pydub import AudioSegment, exceptions
from dataclass import TTSEvent, ChatSpeechEvent, TTSResponse
from asyncio.queues import Queue
from pydub.utils import make_chunks
import os
import json
import io
import time
import pyaudio
import azure.cognitiveservices.speech as speechsdk
import base64


class TTS:
    def __init__(self):
        # speech_config = speechsdk.SpeechConfig(subscription=os.environ.get("SPEECH_KEY"), region=os.environ.get("SPEECH_REGION"))
        # self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        # self.speech_xml = ""
        self._websocket_client = None
        self.is_speaking: bool = False 
    
    async def listen(self):
        async with serve(self._websocket_handler, host='0.0.0.0', port = 9876) as server:
            await server.serve_forever()

    async def _websocket_handler(self, websocket):
        if self._websocket_client is None:
            print("Voice: New client connected")
            self._websocket_client = websocket
            await websocket.wait_closed()
            print("Voice: Client disconnected")
            self._websocket_client = None
        else:
            print("Voice: Client already connected, rejecting new connection")

    async def _recv_message(self):
        if self._websocket_client is None:
            raise Exception("Voice: No client connected")
        try:
            return await self._websocket_client.recv()
        except ConnectionClosed:
            print("Voice: Client is disconnected")
            self._websocket_client = None

    async def _send_message(self, message):

        if self._websocket_client is None:
            raise Exception("Voice: No client connected")
        try: 
            await self._websocket_client.send(message)
        except ConnectionClosed:
            print("Voice: Client is disconnected")
    
    async def generate_tts(self, message: ChatSpeechEvent):
        try:
            payload: TTSEvent = TTSEvent(message.response_text, message.emotions)
            await self._send_message(json.dumps(payload.__dict__))
            res = await self._recv_message()
            res = TTSResponse(**json.loads(res))

            return res
        except Exception as e:
            print("TTS failed for message", message)
            print(e)
            return None


    # async def generate_tts(self, message: str):
    #     try:
    #         future = self.speech_synthesizer.speak_ssml_async(self._format_ssml(message))
    #         loop = asyncio.get_event_loop()
    #         result: speechsdk.SpeechSynthesisResult = await loop.run_in_executor(None, future.get)
    #         if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    #             try: 
    #                 # return await asyncio.to_thread(AudioSegment.from_file, io.BytesIO(result.audio_data))
    #                 return result.audio_data
    #             except exceptions.CouldntDecodeError:
    #                 print("Voice: Failed to decode audio segment")
    #                 return None
    
    #         # something done goofed
    #         elif result.reason == speechsdk.ResultReason.Canceled:
    #             cancellation_details = result.cancellation_details
    #             print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    #             if cancellation_details.reason == speechsdk.CancellationReason.Error:
    #                 if cancellation_details.error_details:
    #                     print("Error details: {}".format(cancellation_details.error_details))
        # except Exception as e:
        #     print("TTS failed for message", message)
        #     print(e)
        #     return None
    

        
# sends message to unity server to be spoken to
async def tts_loop(tts: TTS, tts_queue: Queue, speech_queue):
    while True:
        message: ChatSpeechEvent = await tts_queue.get()
        try:
            start = time.time()
            if message.response_text is not None:
                print("TTS: Generating TTS for message: ", message.response_text)
                res: TTSResponse = await tts.generate_tts(message)
        except asyncio.CancelledError as e:
            raise e
        if res is not None:
            if res.status == "success":
                end = time.time()
                print(f"TTS Time: {end - start - res.time}s")
                message.audio_segment = res
            else:
                print("TTS failed for message: ", message)
        else:
                print("TTS failed for message: ", message)

CHUNK = 4096
def play_audio(seg):
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(seg.sample_width),
                    channels=seg.channels,
                    rate=seg.frame_rate,
                    output=True,
                    frames_per_buffer=CHUNK,
                    # output_device_index=12
                    )
    # Just in case there were any exceptions/interrupts, we release the resource
    # So as not to raise OSError: Device Unavailable should play() be used again
    try:
        # break audio into half-second chunks (to allows keyboard interrupts)
        for chunk in make_chunks(seg, CHUNK):
            stream.write(chunk._data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
