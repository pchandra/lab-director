import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

WAVMIXER_BIN = conf['WAVMIXER_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.INST.value}.wav",
                    f"{Tasks.INST.value}.mp3" ]
    public_keys = [ ]
    if (not force and
        filestore.check_keys(file_id, output_keys, private) and
        filestore.check_keys(file_id, public_keys, public)):
        helpers.destroy_scratch_dir(scratch)
        return

    outfile = f"{scratch}/{Tasks.INST.value}.wav"

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, public)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if this is already tagged instrumental from stemming
    if metadata['instrumental']:
        helpers.destroy_scratch_dir(scratch)
        return

    # Get the info for the original file to get the bit depth
    infofile = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.json", scratch, public)
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
        filename = filestore.retrieve_file(file_id, stem, scratch, private)
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
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.INST.value}.wav", private)

    # Make an MP3 website version
    mp3file = f"{scratch}/{Tasks.INST.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Store the resulting file
    mp3_location = filestore.store_file(file_id, mp3file, f"{Tasks.INST.value}.mp3", private)

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = stored_location
    ret['mp3'] = mp3_location
    helpers.destroy_scratch_dir(scratch)
    return ret
