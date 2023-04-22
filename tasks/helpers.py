import os
import re
import uuid
import wave
import shutil
import subprocess
import json
import soundfile as sf
from config import CONFIG as conf
import taskapi as api

FFMPEG_BIN = conf['FFMPEG_BIN']
WORK_DIR = conf['WORK_DIR']
SILENCE_THRESHOLD = conf['SILENCE_THRESHOLD']
SILENCE_PERCENT = conf['SILENCE_PERCENT']


def setprogress(file_id, task_type, percent=0):
    update = json.dumps({"percent": percent}).encode('ascii')
    api.mark_inprogress(file_id, task_type.value, update)

def get_duration(wavfile):
    # Get the duration of the audio track
    with wave.open(wavfile,'r') as f:
        return f.getnframes() / f.getframerate()

def is_silent(wavfile):
    duration = get_duration(wavfile)
    # Run an FFMPEG cmd to detect silence
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", wavfile,
                     "-af", f"silencedetect=n={SILENCE_THRESHOLD}:d=1",
                     "-f", "null",
                     "-"
                   ])
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Parse stderr, p1/m1 are for detecting total silence, p2/m2 detect mostly silent tracks
    p1 = re.compile('\[silencedetect.*silence_(start|end): ([\d.]+).*')
    p2 = re.compile('\[silencedetect.*silence_duration: ([\d.]+).*')
    silence_total = 0
    count = 0
    start = 0
    end = 0
    for line in stderr.split('\n'):
        m1 = p1.match(line)
        if m1 is not None:
            if m1.group(1) == 'start':
                start = float(m1.group(2))
            else:
                end = float(m1.group(2))
            count += 1
        m2 = p2.match(line)
        if m2 is not None:
            silence_total += float(m2.group(1))

    # Check for 1 interval (1 start, 1 stop) and timecodes match 0 and duration respectively (+/- 1s)
    totally = count == 2 and (start > -1 and start < 1) and (end > (duration-1) and end < (duration+1))
    # Check if total silent time is above our max percent of silence allowed
    mostly = silence_total > (duration * SILENCE_PERCENT)
    return totally, mostly

def get_audio_info(wavfile):
    # Interrogate file and grab some stats about it
    metadata = {}
    info = sf.info(wavfile, verbose=True)
    metadata['size'] = os.path.getsize(wavfile)
    metadata['bit_depth'] = 0
    if info.subtype in ['PCM_S8', 'PCM_U8']:
        metadata['bit_depth'] = 8
    elif info.subtype in ['PCM_16']:
        metadata['bit_depth'] = 16
    elif info.subtype in ['PCM_24']:
        metadata['bit_depth'] = 24
    elif info.subtype in ['PCM_32', 'FLOAT']:
        metadata['bit_depth'] = 32
    elif info.subtype in ['DOUBLE']:
        metadata['bit_depth'] = 64
    metadata['channels'] = info.channels
    metadata['duration'] = info.duration
    metadata['format'] = info.format
    metadata['format_info'] = info.format_info
    metadata['frames'] = info.frames
    metadata['samplerate'] = info.samplerate
    metadata['subtype'] = info.subtype
    metadata['subtype_info'] = info.subtype_info
    metadata['verbose'] = info.extra_info
    return metadata

scratch_dirs = []
def create_scratch_dir():
    path = WORK_DIR + f"/{str(uuid.uuid4())}"
    os.makedirs(path, exist_ok=True)
    scratch_dirs.append(path)
    return path

def destroy_scratch_dir(path):
    if path in scratch_dirs:
        shutil.rmtree(path)
