import os
import re
import wave
import subprocess

import json
import taskapi as api

FFMPEG_BIN = '/usr/local/bin/ffmpeg'

# Working directory for tools to operate
WORK_DIR = '/tmp/SCRATCH'

def setprogress(file_id, task_type, percent=0):
    update = json.dumps({"percent": percent}).encode('ascii')
    api.mark_inprogress(file_id, task_type.value, update)

def is_silent(wavfile):
    # Get the duration of the audio track
    duration = 0
    with wave.open(wavfile,'r') as f:
        duration = f.getnframes() / f.getframerate()
    # Run an FFMPEG cmd to detect silence
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", wavfile,
                     "-af", "silencedetect=n=-36dB:d=1",
                     "-f", "null",
                     "-"
                   ])
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")
    # Parse the output (on stderr)
    p = re.compile('\[silencedetect.*silence_(start|end): ([\d.]+).*')
    count = 0
    start = 0
    end = 0
    for line in stderr.split('\n'):
        m = p.match(line)
        if m is not None:
            if m.group(1) == 'start':
                start = float(m.group(2))
            else:
                end = float(m.group(2))
            count += 1
    # Check for 1 interval (1 start, 1 stop) and timecodes match 0 and duration respectively (+/- 1s)
    return count == 2 and (start > -1 and start < 1) and (end > (duration-1) and end < (duration+1))
