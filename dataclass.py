from dataclasses import dataclass, field
from pydub import AudioSegment

@dataclass
class SpeechEvent:
    response_text: str = field(default=None, compare=False)
    emotions: [str] = field(default=None, compare=False)
    audio_segment: AudioSegment = field(default=None, compare=False)

@dataclass(init = False, order = True)
class ChatSpeechEvent(SpeechEvent):
    priority: int = 0
    user_message: str = field(default=None, compare=False)
    user_name: str = field(default=None, compare=False)
    def __init__(self, user_message, user_name):
        self.response_text = None
        self.audio_segment = None
        self.priority = 0 #TODO: implement priority
        self.user_message = user_message
        self.user_name = user_name