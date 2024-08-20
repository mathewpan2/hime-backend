from dataclasses import dataclass, field
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

@dataclass
class customSpeechRequest:
    type: str = field(default=None)
    response: str = field(default=None)
    emotion: str = field(default=None)
    def __init__(self, response, emotion):
        self.type = "customSpeechRequest"
        self.response = response
        self.emotion = emotion

# helpers
parameters = {
    'model_path': 'gemma-2-2b-it-Q5_K_M.gguf',
    'do_sample': True,
    'n_ctx': 8000,
    'temperature': 0.32,
    'top_p': 0.01,
    'typical_p': 1,
    'epsilon_cutoff': 0,
    'eta_cutoff': 0,
    'n_gpu_layers': -1,
    'tfs': 1,
    'top_a': 0,
    'repetition_penalty': 1.24,
    'encoder_repetition_penalty': 1,
    'top_k': 44,
    'num_beams': 1,
    'penalty_alpha': 0,
    'min_length': 0,
    'length_penalty': 1.0,
    'no_repeat_ngram_size': 0,
    'early_stopping': False,
    'mirostat_mode': 0,
    'mirostat_tau': 5.0,
    'mirostat_eta': 0.1,
}

