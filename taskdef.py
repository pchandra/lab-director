from enum import Enum

class Tasks(Enum):
    KBPM = 'key-bpm'
    STEM = 'stems'
    MAST = 'mastering'
    INST = 'instrumental'
    LYRC = 'lyrics'
    MIDI = 'midi'
    COVR = 'coverart'

class State(Enum):
    INIT = "initial"
    PROG = "in-progress"
    WAIT = "waiting"
    COMP = "completed"
    FAIL = "failed"
    NA = "not-available"
