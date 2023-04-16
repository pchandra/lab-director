import os
import re
import wave
import subprocess
import json
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
