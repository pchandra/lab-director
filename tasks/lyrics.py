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
ML_DEVICE = conf['ML_DEVICE']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ ]
    output_keys = [ ] + public_keys
    output_fmts = [ 'json', 'srt', 'txt']
    for fmt in output_fmts:
        output_keys.append(f"{Tasks.LYRC.value}.{fmt}")
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    outdir = f"{scratch}/{Tasks.LYRC.value}"

    # Get the stem metadata from the filestore
    try:
        stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if stemmer says this is an instrumental
    if metadata['instrumental']:
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Track is an intrumental already')

    # Grab the vocal track to analyze
    try:
        vocalsfile = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}-vocals.mp3", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')

    # Build the command line to run
    cmdline = []
    cmdline.append(WHISPER_BIN)
    cmdline.extend([ "--model", WHISPER_MODEL,
                     "--language", "en",
                     "--device", ML_DEVICE,
                     "--word_timestamps", "True",
                     "--prepend_punctuations", "",
                     "--append_punctuations", "",
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

    # Get duration of audio file to mark progress
    duration = helpers.get_duration(vocalsfile)
    percent = 0
    helpers.setprogress(file_id, Tasks.LYRC, 0)
    while True:
        line = process.stdout.readline()
        stdout += line
        p = re.compile('.*--> ([\d]+):([\d]+)(\.[\d]+)\]')
        m = p.match(line)
        if m is not None:
            timecode = int(m.group(1)) * 60 + int(m.group(2)) + float('0' + m.group(3))
            percent = timecode / duration * 100
            helpers.setprogress(file_id, Tasks.LYRC, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(file_id, Tasks.LYRC, 100)
            break

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    output = {}
    filebase = os.path.splitext(os.path.basename(vocalsfile))[0]
    for fmt in output_fmts:
        output[fmt] = filestore.store_file(file_id, outdir + f"/{filebase}.{fmt}", f"{Tasks.LYRC.value}.{fmt}", private)
    ret['output'] = [ {'type':x,'file':output[x]} for x in output.keys()]
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
