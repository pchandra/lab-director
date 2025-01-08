import os
import json
import time
import subprocess
import taskapi as api
from taskdef import *
from . import helpers
from config import CONFIG as conf

BLEEP_BLASTER_BIN = conf['BLEEP_BLASTER_BIN']
BLEEP_WORD_LIST = conf['BLEEP_WORD_LIST']
WAVMIXER_BIN = conf['WAVMIXER_BIN']

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'beat', 'song', 'batch-item' ]:
        return False, helpers.msg('Track is not a beat, song, or batch-item')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.RDIO.value}.png" ])
    tg.add_private([ f"{Tasks.RDIO.value}.wav",
                     f"{Tasks.RDIO.value}.mp3" ])

    bleep = params.get('bleep', 'silence')
    job_id = params['job_id']

    # Force processing if the user cutlist is present
    user_cutlist = tg.get_file(f"{Tasks.RDIO.value}-cutlist-user.json")
    force = True if user_cutlist else params.get('update', False)

    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    outfile = f"{tg.scratch}/{Tasks.RDIO.value}.wav"
    cutfile = f"{tg.scratch}/{Tasks.RDIO.value}-cutout.json"

    # Get the stem metadata from the filestore
    stem_json = tg.get_file(f"{Tasks.STEM.value}.json")
    if stem_json is None:
        if tg.status['original']['status'] != "failed":
            api.requeue_ondemand(job_id, Tasks.LYRC.value)
            return False, helpers.msg(f'Input file not found, requeuing task: {Tasks.STEM.value}.json')
        return False, helpers.msg(f'Original failed, not requeuing task')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if this is already tagged instrumental from stemming
    if metadata['instrumental']:
        return False, helpers.msg('Track is an intrumental already')

    # Build the command to bleep the vocal track
    cmdline = []
    cmdline.append(BLEEP_BLASTER_BIN)

    # Handle user cutist
    if user_cutlist:
        cmdline.extend([ "-u", user_cutlist ])
    # Handle normal case
    else:
        lyric_file = tg.get_file(f"{Tasks.LYRC.value}.json")
        if lyric_file is None:
            api.requeue_ondemand(job_id, Tasks.RDIO.value)
            return False, helpers.msg(f'Input file not found, requeuing: {Tasks.LYRC.value}.json')
        cmdline.extend([ "-l", lyric_file,
                         "-w", BLEEP_WORD_LIST,
                         "-c", cutfile
                       ])

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

    vocalout = f"{tg.scratch}/edit.wav"

    cmdline.extend([ "-b", bleep,
                     "-B", "5",
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
    sample_rate = info['streams'][0]['sample_rate']

    outfile = f"{tg.scratch}/{Tasks.RDIO.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile,
                     "-b", str(bitdepth),
                     "-r", str(sample_rate)
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
    if not user_cutlist:
        ret['cutout'] = tg.put_file(cutfile, f"{Tasks.RDIO.value}-cutlist-auto.json")

    # Make an MP3 website version
    mp3file = f"{tg.scratch}/{Tasks.RDIO.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Make a temp PNG for it
    helpers.make_wave_png(mp3file)
    # Store the resulting files
    ret['mp3'] = tg.put_file(mp3file, f"{Tasks.RDIO.value}.mp3")
    ret['png'] = tg.put_file(mp3file + ".png", f"{Tasks.RDIO.value}.png")
    # Remove inprogress marker files
    tg.remove_file(f"{Tasks.RDIO.value}.temp")
    return True, ret
