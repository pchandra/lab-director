import os
import re
import json
import time
import wave
import subprocess
import taskapi as api
from taskdef import *
from . import helpers
from config import CONFIG as conf

WHISPER_BIN = conf['WHISPER_BIN']
WHISPER_MODEL = conf['WHISPER_MODEL']
ML_DEVICE = conf['ML_DEVICE']

def ondemand(tg, params, force=False):
    # Hack to check if a run is in progress already
    tg.add_private([ f"{Tasks.LYRC.value}.altemp" ])
    if not force and tg.check_keys():
        return True, helpers.msg('In progress already')
    tg.priv_keys.remove(f"{Tasks.LYRC.value}.altemp")

    if tg.status['type'] not in [ 'beat', 'song' ]:
        return False, helpers.msg('Track is not a beat or song')
    # Short-circuit if the filestore already has assets we would produce
    output_fmts = [ 'json', 'srt', 'txt']
    for fmt in output_fmts:
        tg.add_private([ f"{Tasks.LYRC.value}.{fmt}" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Write the inprogress temp file, upload it, and delete it
    tempfile = f"{tg.scratch}/{Tasks.LYRC.value}.altemp"
    with open(tempfile, 'w') as f:
        f.write("inprogress")
    tg.put_file(tempfile, f"{Tasks.LYRC.value}.altemp")
    os.remove(tempfile)

    job_id = params['job_id']

    # Get the stem metadata from the filestore
    stem_json = tg.get_file(f"{Tasks.STEM.value}.json")
    if stem_json is None:
        tg.remove_file(f"{Tasks.LYRC.value}.altemp")
        api.requeue_ondemand(job_id, Tasks.LYRC.value)
        return False, helpers.msg(f'Input file not found, requeuing task: {Tasks.STEM.value}.json')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if stemmer says this is an instrumental
    if metadata['instrumental']:
        return False, helpers.msg('Track is an intrumental already')

    language = params.get('language', 'en')

    outdir = f"{tg.scratch}/{Tasks.LYRC.value}"

    # Grab the vocal track to analyze
    vocalsfile = tg.get_file(f"{Tasks.STEM.value}-vocals.mp3")
    if vocalsfile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.STEM.value}-vocals.mp3')

    # Build the command line to run
    cmdline = []
    cmdline.append(WHISPER_BIN)
    cmdline.extend([ "--model", WHISPER_MODEL,
                     "--language", language,
                     "--device", ML_DEVICE,
                     "--accurate",
                     "--vad", "True",
                     "--detect_disfluencies", "True",
                     "--punctuations_with_words", "False",
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

    helpers.setprogress(tg.file_id, Tasks.LYRC, 0)
    while True:
        line = process.stderr.readline()
        stderr += line
        p = re.compile('[\s]*([\d]+)%')
        m = p.match(line)
        if m is not None:
            percent = int(m.group(1))
            helpers.setprogress(tg.file_id, Tasks.LYRC, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(tg.file_id, Tasks.LYRC, 100)
            break

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    output = {}
    filebase = os.path.basename(vocalsfile)
    for fmt in output_fmts:
        ext = 'words.json' if fmt == 'json' else fmt
        output[fmt] = tg.put_file(outdir + f"/{filebase}.{ext}", f"{Tasks.LYRC.value}.{fmt}")
    ret['output'] = [ {'type':x,'file':output[x]} for x in output.keys()]
    # Remove inprogress marker files
    tg.remove_file(f"{Tasks.LYRC.value}.temp")
    tg.remove_file(f"{Tasks.LYRC.value}.altemp")
    return True, ret
