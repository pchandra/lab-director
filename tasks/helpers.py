import os
import re
import uuid
import time
from datetime import datetime
import shutil
import subprocess
import traceback
import json
import soundfile as sf
from . import filestore
from config import CONFIG as conf
import taskapi as api

FFMPEG_BIN = conf['FFMPEG_BIN']
FFPROBE_BIN = conf['FFPROBE_BIN']
BARTENDER_BIN = conf['BARTENDER_BIN']
WORK_DIR = conf['WORK_DIR']
SILENCE_THRESHOLD = conf['SILENCE_THRESHOLD']
SILENCE_PERCENT = conf['SILENCE_PERCENT']
FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_BATCH = conf['FILESTORE_BATCH']
FILESTORE_BEATS = conf['FILESTORE_BEATS']
FILESTORE_SONGS = conf['FILESTORE_SONGS']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']
FILESTORE_ARTISTS = conf['FILESTORE_ARTISTS']


def msg(msg, base={}):
    base['message'] = f"{msg}"
    return base

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

def make_nonsilent_wave(wavfile):
    # Build the command line to run
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", wavfile,
                     "-af", "silenceremove=stop_periods=-1:stop_duration=0.1:stop_threshold=-36dB",
                     "-ac", "1",
                     "-ss", "0",
                     wavfile + '.wav', "-y"
                   ])
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)
    process.wait()
    return wavfile + '.wav'

def make_website_mp3(infile, mp3file, high_quality=False):
    quality = [ "-b:a", "320k" ] if high_quality else [ "-q:a", "2" ]
    # Run an FFMPEG cmd to compress to mp3
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", infile,
                     "-v", "quiet",
                     quality[0], quality[1],
                     "-y"
                   ])
    cmdline.append(mp3file)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

def make_sample_rate(infile, sampfile, sample_rate, bit_depth=16, channels=2):
    codec = 'pcm_s16le'
    if bit_depth == 8:
        codec = 'pcm_u8'
    elif bit_depth == 24:
        codec = 'pcm_s24le'
    elif bit_depth == 32:
        codec = 'pcm_s32le'

    # Run an FFMPEG cmd to compress to mp3
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", infile,
                     "-v", "quiet",
                     "-ac", str(channels),
                     "-acodec", codec,
                     "-ar", str(sample_rate),
                     "-y"
                   ])
    cmdline.append(sampfile)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")


class TaskGuard:
    def __init__(self, file_id, task, force=False):
        self.file_id = file_id
        self.task = task
        self.force = force
        self.pub_keys = []
        self.priv_keys = []
        self.success = False
        self.start = 0
        self.stop = 0

    def __enter__(self):
        self.start = time.time()
        self.status = api.get_status(self.file_id)
        self.private, self.public = self._get_bucketnames()
        self._create_scratch_dir()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_tb != None:
            traceback.print_tb(exc_tb)
        try:
            if self.success:
                self.copy_keys()
            self._destroy_scratch_dir()
            self.stop = time.time()
            return True
        except:
            pass
        else:
            self.stop = time.time()
            return False


    def _create_scratch_dir(self):
        self.scratch = WORK_DIR + f"/{str(uuid.uuid4())}"
        os.makedirs(self.scratch, exist_ok=True)

    def _destroy_scratch_dir(self):
        shutil.rmtree(self.scratch)

    def _get_bucketnames(self):
        private = FILESTORE_BATCH
        if self.status['type'] == 'beat':
            private = FILESTORE_BEATS
        elif self.status['type'] == 'song':
            private = FILESTORE_SONGS
        elif self.status['type'] == 'soundkit':
            private = FILESTORE_SOUNDKITS
        elif self.status['type'] == 'artist':
            private = FILESTORE_ARTISTS
        return private, FILESTORE_PUBLIC

    def remove_file(self, key):
        return filestore.remove_file(self.file_id, key, self.private)

    def get_file(self, key):
        return filestore.retrieve_file(self.file_id, key, self.scratch, self.private)

    def put_file(self, file, key):
        return filestore.store_file(self.file_id, file, key, self.private)

    def iterate_files(self):
        return filestore.iterate_objects(self.file_id, self.private)

    def add_public(self, keys):
        self.priv_keys += keys
        self.pub_keys += keys

    def add_private(self, keys):
        self.priv_keys += keys

    def check_keys(self):
        if filestore.check_keys(self.file_id, self.priv_keys, self.private):
            self.copy_keys()
            return True
        return False

    def copy_keys(self):
        if self.status['type'] == 'batch-item':
            return
        if self.force or not filestore.check_keys(self.file_id, self.pub_keys, self.public):
            filestore.copy_keys(self.file_id, self.pub_keys, self.private, self.public)

    def copy_file(self, srckey, dstkey):
        filestore.copy_object(self.file_id, srckey, dstkey, self.private)

    def get_perf(self):
        ret = {}
        ret['start'] = datetime.fromtimestamp(self.start).strftime('%Y-%m-%d %H:%M:%S')
        ret['stop'] = datetime.fromtimestamp(self.stop).strftime('%Y-%m-%d %H:%M:%S')
        ret['time_start'] = self.start
        ret['time_stop'] = self.stop
        ret['time_elapsed'] = self.stop - self.start
        return ret
