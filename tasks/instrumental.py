import os
import re
import subprocess
from taskdef import *
from . import helpers

WAVMIXER_BIN = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

DEMUCS_MODEL="htdemucs_6s"

def _get_model():
    # This is the model name we'll run, must be one of:
    #   htdemucs_6s htdemucs htdemucs_ft mdx mdx_extra hdemucs_mmi
    return DEMUCS_MODEL

def _stems_for_model(model):
    stems = [ "bass", "drums", "other", "vocals"]
    if model == "htdemucs_6s":
        stems.append("guitar")
        stems.append("piano")
    return stems

def execute(filename, status):
    model = _get_model()
    stems = _stems_for_model(model)
    outfile = f"{helpers.WORK_DIR}/{os.path.basename(filename)}-{Tasks.INST.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(WAVMIXER_BIN)
    cmdline.extend([ "-o", outfile ])
    # Add all the stems except the vocal track
    stems.remove("vocals")
    for stem in stems:
        cmdline.append(status[Tasks.STEM.value][State.COMP.value][model][stem])
    # Execute the command if we don't already have output
    stdout = None
    stderr = None
    if Tasks.INST.value in status and State.COMP.value in status[Tasks.INST.value] and "stdout" in status[Tasks.INST.value][State.COMP.value]:
        stdout = status[Tasks.INST.value][State.COMP.value]["stdout"]
        stderr = status[Tasks.INST.value][State.COMP.value]["stderr"]
    if not os.path.exists(outfile):
        # Connect stdin to prevent hang when in background
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
