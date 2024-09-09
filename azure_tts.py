import azure.cognitiveservices.speech as speechsdk
import asyncio
from asyncio.queues import Queue
from dataclass import HimeSpeechEvent, UnitySpeechEvent
import time
import os

class TTS:
    def __init__(self):
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get("SPEECH_KEY"), region=os.environ.get("SPEECH_REGION"))
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Ogg48Khz16BitMonoOpus)
        audio_config = speechsdk.audio.AudioOutputConfig(filename="tts.wav")
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        self.speech_xml = ""

        with open(os.path.join("data", "ssml.xml"), "r") as f:
            self.speech_xml = f.read()
    
    def _format_ssml(self, message: str, emotion: str):
        return self.speech_xml.replace("[text]", message).replace("[emotion]", f"\"{emotion}\"")


    
    async def generate_tts(self, message: str, emotion: str):
        try:
            future = self.speech_synthesizer.speak_ssml_async(self._format_ssml(message, emotion))
            loop = asyncio.get_event_loop()
            result: speechsdk.SpeechSynthesisResult = await loop.run_in_executor(None, future.get)
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
                # try: 
                #     # return await asyncio.to_thread(AudioSegment.from_file, io.BytesIO(result.audio_data))
                #     return result.audio_data
                # # except exceptions.CouldntDecodeError:
                # #     print("Voice: Failed to decode audio segment")
                # #     return None
    
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

async def tts_loop(tts: TTS, tts_queue: Queue, speech_queue: Queue):
    while True:
        message: HimeSpeechEvent = await tts_queue.get()
        try:
            if message.type == "EndSpeech":
                print("TTS: EndSpeech received")
                speech_queue.put_nowait(UnitySpeechEvent("EndSpeech", "EndSpeech", "EndSpeech", None))
                continue

            print("TTS: Generating TTS for message: ", message.response)
            start = time.time()
            if message.platform == "chat" and message.type == "NewSpeech":
                message.response = message.prompt + " " + message.response
            res = await tts.generate_tts(message.response, message.emotion)
            if res is not None:
                speech_queue.put_nowait(UnitySpeechEvent(message.type, message.response, message.emotion, res))
            end = time.time()
            print(f"TTS Time: {end - start}s for message: {message.response}")
        except asyncio.CancelledError as e:
            raise e

            
        

# CHUNK = 4096
# def play_audio(seg):
#     p = pyaudio.PyAudio()
#     stream = p.open(format=p.get_format_from_width(seg.sample_width),
#                     channels=seg.channels,
#                     rate=seg.frame_rate,
#                     output=True,
#                     frames_per_buffer=CHUNK,
#                     # output_device_index=12
#                     )
#     # Just in case there were any exceptions/interrupts, we release the resource
#     # So as not to raise OSError: Device Unavailable should play() be used again
#     try:
#         # break audio into half-second chunks (to allows keyboard interrupts)
#         for chunk in make_chunks(seg, CHUNK):
#             stream.write(chunk._data)
#     finally:
#         stream.stop_stream()
#         stream.close()
#         p.terminate()