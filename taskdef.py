import time
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

def _run_key_bpm_finder(filebase):
    time.sleep(30)

def _run_demucs(filebase):
    time.sleep(30)

def _run_phaselimiter(filebase):
    time.sleep(30)

def _run_wav_mixer(filebase):
    time.sleep(30)

def _run_whisper(filebase):
    time.sleep(30)

def _run_basic_pitch(filebase):
    time.sleep(30)

def _run_dalle2(filebase):
    time.sleep(30)

RUNTASK = {}
RUNTASK[Tasks.KBPM] = _run_key_bpm_finder
RUNTASK[Tasks.STEM] = _run_demucs
RUNTASK[Tasks.MAST] = _run_phaselimiter
RUNTASK[Tasks.INST] = _run_wav_mixer
RUNTASK[Tasks.LYRC] = _run_whisper
RUNTASK[Tasks.MIDI] = _run_basic_pitch
RUNTASK[Tasks.COVR] = _run_dalle2
