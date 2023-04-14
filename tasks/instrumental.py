import os
import re
import subprocess
from taskdef import *
from . import helpers

WAVMIXER_BIN = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

def execute(filename, status):
    outfile = f"{helpers.WORK_DIR}/{os.path.basename(filename)}-{Tasks.INST.value}.wav"
    # Return quickly if this is already tagged instrumental from stemming
    if status[Tasks.STEM.value][State.COMP.value]['instrumental']:
        return {}

    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile ])

    # Create the track from everything but the vocals
    stems = status[Tasks.STEM.value][State.COMP.value]['stems'].keys()
    for stem in stems:
        if stem == "vocals":
            continue
        cmdline.append(status[Tasks.STEM.value][State.COMP.value]['stems'][stem])

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
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = outfile
    return ret
