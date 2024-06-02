from dataclasses import dataclass, field
from pydub import AudioSegment
from typing import List

@dataclass(init = False, order = True)
class ChatSpeechEvent():
    priority: int = 0
    user_message: str = field(default=None, compare=False)
    user_name: str = field(default=None, compare=False)
    response_text: str = field(default=None, compare=False)
    emotions: List[str] = field(default_factory=None, compare=False)
    def __init__(self, user_message, user_name):
        self.response_text = None
        self.priority = 0 #TODO: implement priority
        self.emotions = []
        self.user_message = user_message
        self.user_name = user_name


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
