from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import asyncio
from pydub import AudioSegment, exceptions
from pydub.utils import make_chunks
from aiohttp import ClientSession
import os
import json
import io
import time
import pyaudio
import azure.cognitiveservices.speech as speechsdk

# class TTS:
#     def __init__(self):
#         self._websocket_client = None
    
#     async def listen(self):
#         async with serve(self._websocket_handler, host='0.0.0.0', port = 9876) as server:
#             await server.serve_forever()

#     async def _websocket_handler(self, websocket):
#         if self._websocket_client is None:
#             print("Voice: New client connected")
#             self._websocket_client = websocket
#             await websocket.wait_closed()
#             print("Voice: Client disconnected")
#             self._websocket_client = None
#         else:
#             print("Voice: Client already connected, rejecting new connection")

#     async def _recv_message(self):
#         if self._websocket_client is None:
#             raise Exception("Voice: No client connected")
#         try:
#             return await self._websocket_client.recv()
#         except ConnectionClosed:
#             print("Voice: Client is disconnected")
#             self._websocket_client = None

#     async def _send_message(self, message):

#         if self._websocket_client is None:
#             raise Exception("Voice: No client connected")
#         try: 
#             await self._websocket_client.send(message)
#         except ConnectionClosed:
#             print("Voice: Client is disconnected")
#             self._websocket_client = None

#     async def generate_tts(self, message):
#         if self._websocket_client is None:
#             raise Exception("Voice: No client connected")
#         try:
#             request = {"message": message.response_text}
#             await self._send_message(json.dumps(request))
#             audio_bytes = await self._recv_message()

#             if audio_bytes is None:
#                 print("Voice: No audio segment received")
#                 return None
#         except ConnectionClosed:
#             print("Voice: Client is disconnected")
#             self._websocket_client = None
#         try: 
#             return await asyncio.to_thread(AudioSegment.from_file, io.BytesIO(audio_bytes), format="wav")
#         except exceptions.CouldntDecodeError:
#             print("Voice: Failed to decode audio segment")
#             return None


class TTS:
    def __init__(self):
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get("SPEECH_KEY"), region=os.environ.get("SPEECH_REGION"))
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        self.speech_xml = ""

        with open("ssml.xml", "r") as file:
            self.speech_xml = file.read()
        
    def _format_ssml(self, message: str):
        return self.speech_xml.replace("[text]", message)

    async def generate_tts(self, message: str):
        try:
            future = self.speech_synthesizer.speak_ssml_async(self._format_ssml(message))
            loop = asyncio.get_event_loop()
            result: speechsdk.SpeechSynthesisResult = await loop.run_in_executor(None, future.get)
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                try: 
                    return await asyncio.to_thread(AudioSegment.from_file, io.BytesIO(result.audio_data))
                except exceptions.CouldntDecodeError:
                    print("Voice: Failed to decode audio segment")
                    return None
    
            # something done goofed
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print("Speech synthesis canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    if cancellation_details.error_details:
                        print("Error details: {}".format(cancellation_details.error_details))
        except Exception as e:
            print("TTS failed for message", message)
            print(e)
            return None

        

async def tts_loop(voice, tts_queue, speech_queue):
    while True:
        message = await tts_queue.get()
        try:
            start = time.time()
            res: AudioSegment = await voice.generate_tts(message.response_text)
        except asyncio.CancelledError as e:
            raise e
        if res is not None:
            end = time.time()
            print(f"TTS Time: {end - start}s")
            message.audio_segment = res
            await speech_queue.put(message)
        else:
            print("TTS failed for message", message)
    # message -> chat_messages -> response from llm -> tts_queue -> voice websocket -> back here

async def speech_loop(speech_queue):
    while True:
        message = await speech_queue.get()
        print(f"Speech: {message.response_text}")
        if message.audio_segment is not None:
            play_audio(message.audio_segment)
        else:
            print("Speech: No audio segment for message", message)

CHUNK = 4096
def play_audio(seg):
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(seg.sample_width),
                    channels=seg.channels,
                    rate=seg.frame_rate,
                    output=True,
                    frames_per_buffer=CHUNK,
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
