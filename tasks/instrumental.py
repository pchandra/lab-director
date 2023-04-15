import os
import re
import subprocess
from taskdef import *
from . import helpers
from . import filestore

WAVMIXER_BIN = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

def execute(file_id, status):
    outfile = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.INST.value}.wav"
    # Return quickly if this is already tagged instrumental from stemming
    if status[Tasks.STEM.value][State.COMP.value]['instrumental']:
        return {}

    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile ])

    # Grab all the stems
    filenames = []
    for stem in status[Tasks.STEM.value][State.COMP.value]['output']:
        if stem['type'] == "vocals":
            continue
        filename = filestore.retrieve_file(file_id, status, f"stem-{stem['type']}.wav", helpers.WORK_DIR + f"/{status['uuid']}")
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
    stored_location = filestore.store_file(file_id, status, outfile, 'instrumental.wav')

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = stored_location
    return ret
