import os
import re
import json
import wave
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

WHISPER_BIN = conf['WHISPER_BIN']
WHISPER_MODEL = conf['WHISPER_MODEL']

def execute(file_id, status, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = []
    output_fmts = [ 'json', 'srt', 'tsv', 'vtt', 'txt']
    for fmt in output_fmts:
        output_keys.append(f"{Tasks.LYRC.value}.{fmt}")
    if not force and filestore.check_keys(file_id, status, output_keys):
        return

    # Proceed with running this task
    outdir = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.LYRC.value}"

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, status, f"{Tasks.STEM.value}.json", helpers.WORK_DIR + f"/{status['uuid']}")
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if stemmer says this is an instrumental
    if metadata['instrumental']:
        return

    # Grab the vocal track to analyze
    vocalsfile = filestore.retrieve_file(file_id, status, f"{Tasks.STEM.value}-vocals.wav", helpers.WORK_DIR + f"/{status['uuid']}")

    # Build the command line to run
    cmdline = []
    cmdline.append(WHISPER_BIN)
    cmdline.extend([ "--model", WHISPER_MODEL,
                     "--language", "en",
                     "--output_dir", outdir
                   ])
    cmdline.append(vocalsfile)
    # Execute the command if we don't already have output
    stdout = ""
    stderr = ""
    # Connect stdin to prevent hang when in background
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    process.stdin.write("\n\n\n\n\n")

    # Get duration of audio file
    duration = 0
    with wave.open(vocalsfile,'r') as f:
        duration = f.getnframes() / f.getframerate()
    percent = 0
    helpers.setprogress(status['id'], Tasks.LYRC, 0)
    while True:
        line = process.stdout.readline()
        stdout += line
        p = re.compile('.*--> ([\d]+):([\d]+)(\.[\d]+)\]')
        m = p.match(line)
        if m is not None:
            timecode = int(m.group(1)) * 60 + int(m.group(2)) + float('0' + m.group(3))
            percent = timecode / duration * 100
            helpers.setprogress(status['id'], Tasks.LYRC, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(status['id'], Tasks.LYRC, 100)
            break

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    output = {}
    filebase = os.path.splitext(os.path.basename(vocalsfile))[0]
    for fmt in output_fmts:
        output[fmt] = filestore.store_file(file_id, status, outdir + f"/{filebase}.{fmt}", f"{Tasks.LYRC.value}.{fmt}")
    ret['output'] = [ {'type':x,'file':output[x]} for x in output.keys()]
    return ret
