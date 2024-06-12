from dataclasses import dataclass, field
from pydub import AudioSegment
from typing import List


# general chat 
@dataclass(init = False, order = True)
class ChatSpeechEvent():
    priority: int = 0
    user_message: str = field(default=None, compare=False)
    user_name: str = field(default=None, compare=False)
    def __init__(self, user_message, user_name):
        self.priority = 0 #TODO: implement priority
        self.user_message = user_message
        self.user_name = user_name



@dataclass
class HimeSpeechEvent():
    type: str = field(default=None)
    prompt: str = field(default=None)
    response: str = field(default=None)
    emotion: str = field(default=None)



# response hime-ai
@dataclass
class HimeResponse():
    result: str = field(default=None)
    type: str = field(default=None)
    response: str = field(default=None)
    def __init__(self, result, type, response):
        self.result = result
        self.type = type
        self.response = response


# Unity
@dataclass
class UnitySpeechEvent():
    type: str = field(default=None)
    response: str = field(default=None)
    emotion: str = field(default=None)
    audio: bytes = field(default=None)

@dataclass
class TTSEvent:
    message : str = field(default=None, compare=False)
    emotions: List[str] = field(default=None, compare=False)
    def __init__(self, message, emotions):
        self.message = message
        self.emotions = emotions

@dataclass
class TTSResponse:
    status: str = field(default=None, compare=False)
    time: float = field(default=None, compare=False)

# Control Panel: last message

@dataclass
class getCurrentResponse:
    type: str = field(default=None)
    response: str = field(default=None)
    def __init__(self, response):
        self.type = "getCurrentResponse"
        self.response = response

@dataclass
class customSpeechRequest:
    type: str = field(default=None)
    response: str = field(default=None)
    emotion: str = field(default=None)
    def __init__(self, response, emotion):
        self.type = "customSpeechRequest"
        self.response = response
        self.emotion = emotion

