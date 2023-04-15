import os
import re
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore

WAVMIXER_BIN = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

def execute(file_id, status, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.INST.value}.wav" ]
    if not force and filestore.check_keys(file_id, status, output_keys):
        return

    # Proceed with running this task
    outfile = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.INST.value}.wav"

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, status, f"{Tasks.STEM.value}.json", helpers.WORK_DIR + f"/{status['uuid']}")
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    # Return quickly if this is already tagged instrumental from stemming
    if metadata['instrumental']:
        return

    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile ])

    # Grab all the stems
    filenames = []
    for stem in status[Tasks.STEM.value][State.COMP.value]['output']:
        if stem['type'] == "vocals":
            continue
        filename = filestore.retrieve_file(file_id, status, f"{Tasks.STEM.value}-{stem['type']}.wav", helpers.WORK_DIR + f"/{status['uuid']}")
        filenames.append(filename)
    if len(filenames) > 0:
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
    stored_location = filestore.store_file(file_id, status, outfile, f"{Tasks.INST.value}.wav")

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = stored_location
    return ret
