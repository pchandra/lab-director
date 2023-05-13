import os
import re
import uuid
import shutil
import subprocess
import json
import soundfile as sf
from config import CONFIG as conf
import taskapi as api

FFMPEG_BIN = conf['FFMPEG_BIN']
FFPROBE_BIN = conf['FFPROBE_BIN']
BARTENDER_BIN = conf['BARTENDER_BIN']
WORK_DIR = conf['WORK_DIR']
SILENCE_THRESHOLD = conf['SILENCE_THRESHOLD']
SILENCE_PERCENT = conf['SILENCE_PERCENT']


def setprogress(file_id, task_type, percent=0):
    update = json.dumps({"percent": percent}).encode('ascii')
    api.mark_inprogress(file_id, task_type.value, update)

def get_duration(wavfile):
    # Get the duration of the audio track
    info = get_media_info(wavfile)
    return float(info['streams'][0]['duration'])

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

def get_media_info(wavfile):
    # Build the command line to run
    cmdline = []
    cmdline.append(FFPROBE_BIN)
    cmdline.extend([ "-v", "quiet",
                     "-of", "json",
                     "-show_format",
                     "-show_streams",
                     "-show_chapters",
                     "-show_programs",
                     "-find_stream_info"
                   ])
    cmdline.append(wavfile)
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Validate and write JSON output to tempfile
    return json.loads(stdout)

def make_wave_png(wavfile, factor=None):
    # Build the command line to run
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", wavfile,
                     "-o", "/dev/null",
                     "-p", wavfile + ".png",
                     "-F", wavfile + ".json",
                     "-b", "2000",
                     "-H", "200",
                     "-W", "2000",
                     "-m"
                   ])
    if factor is not None:
        cmdline.extend(["-f", str(factor)])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    ret = 0
    with open(wavfile + ".json") as f:
        ret = json.load(f)['factor']
    return ret

scratch_dirs = []
def create_scratch_dir():
    path = WORK_DIR + f"/{str(uuid.uuid4())}"
    os.makedirs(path, exist_ok=True)
    scratch_dirs.append(path)
    return path

def destroy_scratch_dir(path):
    if path in scratch_dirs:
        shutil.rmtree(path)
