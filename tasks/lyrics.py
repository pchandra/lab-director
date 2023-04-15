import os
import re
import json
import wave
import subprocess
from taskdef import *
from . import helpers
from . import filestore

WHISPER_BIN = '/usr/local/bin/whisper'

def execute(file_id, status):
    outdir = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.LYRC.value}"
    # Return quickly if stemmer says this is an instrumental
    if status[Tasks.STEM.value][State.COMP.value]['instrumental']:
        return {}

    # Grab the vocal track to analyze
    vocalsfile = filestore.retrieve_file(file_id, status, f"stem-vocals.wav", helpers.WORK_DIR + f"/{status['uuid']}")

    # Build the command line to run
    cmdline = []
    cmdline.append(WHISPER_BIN)
    cmdline.extend([ "--model", "medium",
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
    output['json'] = filestore.store_file(file_id, status, outdir + f"/{os.path.basename(vocalsfile)}.json", 'lyrics.json')
    output['srt'] = filestore.store_file(file_id, status, outdir + f"/{os.path.basename(vocalsfile)}.srt", 'lyrics.srt')
    output['txt'] = filestore.store_file(file_id, status, outdir + f"/{os.path.basename(vocalsfile)}.txt", 'lyrics.txt')
    ret['output'] = [ {'type':x,'file':output[x]} for x in output.keys()]
    return ret
