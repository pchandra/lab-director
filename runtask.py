import time
import json
import subprocess
from taskdef import *
import taskapi as api

# Working directory for tools to operate
WORK_DIR = '/tmp'

_task_bin = {}
_task_bin[Tasks.KBPM] = '/Users/chandra/ll/co/key-bpm-finder/keymaster-json.py'
_task_bin[Tasks.STEM] = '/usr/local/bin/demucs'
_task_bin[Tasks.MAST] = '/Users/chandra/ll/co/phaselimiter/bin/Release/phase_limiter'
_task_bin[Tasks.INST] = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'
_task_bin[Tasks.LYRC] = '/usr/local/bin/whisper'
_task_bin[Tasks.MIDI] = '/usr/local/bin/basic-pitch'
_task_bin[Tasks.COVR] = '/bin/echo'

def _run_key_bpm_finder(filebase):
    cmdline = []
    cmdline.append('/usr/local/bin/python3.9')
    cmdline.append(_task_bin[Tasks.KBPM])
    cmdline.append(filebase)
    process = subprocess.Popen(cmdline, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    return json.loads(stdout)

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

execute = {}
execute[Tasks.KBPM] = _run_key_bpm_finder
execute[Tasks.STEM] = _run_demucs
execute[Tasks.MAST] = _run_phaselimiter
execute[Tasks.INST] = _run_wav_mixer
execute[Tasks.LYRC] = _run_whisper
execute[Tasks.MIDI] = _run_basic_pitch
execute[Tasks.COVR] = _run_dalle2
