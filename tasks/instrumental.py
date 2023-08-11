import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

WAVMIXER_BIN = conf['WAVMIXER_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'beat', 'song' ]:
        return False, helpers.msg('Track is not a beat or song')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.INST.value}.png" ])
    tg.add_private([ f"{Tasks.INST.value}.wav",
                     f"{Tasks.INST.value}.mp3" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    outfile = f"{tg.scratch}/{Tasks.INST.value}.wav"

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

    # Get the info for the original file to get the bit depth
    infofile = tg.get_file(f"{Tasks.ORIG.value}.json")
    if infofile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.json')
    with open(infofile, 'r') as f:
        info = json.load(f)
    bitdepth = info['streams'][0]['bits_per_sample']

    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile,
                     "-b", str(bitdepth)
                   ])

    # Grab all the stems
    filenames = []
    for stem in metadata['stems-core']:
        if stem == f'{Tasks.STEM.value}-vocals.wav':
            continue
        filename = tg.get_file(stem)
        if filename is None:
            return False, helpers.msg(f'Input file not found: {stem}')
        filenames.append(filename)
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

    # Store the resulting file
    stored_location = tg.put_file(outfile, f"{Tasks.INST.value}.wav")

    # Make an MP3 website version
    mp3file = f"{tg.scratch}/{Tasks.INST.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Make a temp PNG for it
    helpers.make_wave_png(mp3file)
    # Store the resulting files
    mp3_location = tg.put_file(mp3file, f"{Tasks.INST.value}.mp3")
    png_location = tg.put_file(mp3file + ".png", f"{Tasks.INST.value}.png")

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = stored_location
    ret['mp3'] = mp3_location
    ret['png'] = png_location
    return True, ret
