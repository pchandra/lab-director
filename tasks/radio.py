import os
import json
import subprocess
from taskdef import *
from config import CONFIG as conf

BLEEP_BLASTER_BIN = conf['BLEEP_BLASTER_BIN']
BLEEP_WORD_LIST = conf['BLEEP_WORD_LIST']
WAVMIXER_BIN = conf['WAVMIXER_BIN']

def ondemand(tg, params, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_private([ f"{Tasks.RDIO.value}.wav" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    bleep = params['bleep']
    job_id = params['job_id']

    outfile = f"{tg.scratch}/{Tasks.RDIO.value}.wav"

    # Get the stem metadata from the filestore
    stem_json = tg.get_file(f"{Tasks.STEM.value}.json")
    if stem_json is None:
        return False, helpers.msg(f'Input file not found: {Tasks.STEM.value}.json')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if this is already tagged instrumental from stemming
    if metadata['instrumental']:
        return False, helpers.msg('Track is an intrumental already')

    # Grab all the stems
    filenames = []
    vocals = None
    for stem in metadata['stems-core']:
        filename = tg.get_file(stem)
        if filename is None:
            return False, helpers.msg(f'Input file not found: {stem}')
        if stem == f'{Tasks.STEM.value}-vocals.wav':
            vocals = filename
            continue
        filenames.append(filename)

    lyric_file = tg.get_file(f"{Tasks.LYRC.value}.json")

    vocalout = f"{tg.scratch}/edit.wav"
    # Execute the command to bleep the vocal track
    cmdline = []
    cmdline.append(BLEEP_BLASTER_BIN)

    cmdline.extend([ "-l", lyric_file,
                     "-b", bleep,
                     "-w", BLEEP_WORD_LIST,
                     "-m", "3",
                     "-o", vocalout
                   ])
    cmdline.append(vocals)

    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Build the dict to return to caller
    ret = { "bleep_command": { "stdout": stdout, "stderr": stderr } }

    # Add the edited vocals to the file list
    filenames.append(vocalout)

    # Get the info for the original file to get the bit depth
    infofile = tg.get_file(f"{Tasks.ORIG.value}.json")
    if infofile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.json')
    with open(infofile, 'r') as f:
        info = json.load(f)
    bitdepth = info['streams'][0]['bits_per_sample']

    outfile = f"{tg.scratch}/{Tasks.RDIO.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile,
                     "-b", str(bitdepth)
                   ])
    cmdline.extend(filenames)

    # Connect stdin to prevent hang when in background
    stdout = None
    stderr = None
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Build the dict to return to caller
    ret['mixer'] = { "stdout": stdout, "stderr": stderr }
    ret['output'] = tg.put_file(outfile, f"{Tasks.RDIO.value}.wav")
    return True, ret
