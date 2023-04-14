import os
import re
import subprocess
from taskdef import *
from . import helpers

DEMUCS_BIN = '/usr/local/bin/demucs'
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
    outbase = f"{helpers.WORK_DIR}/{model}/{os.path.basename(filename)}"
    # Build the command line to run
    cmdline = []
    cmdline.append(DEMUCS_BIN)
    cmdline.extend([ "-d", "cpu",
                     "-n", model,
                     "-o", helpers.WORK_DIR,
                     "--filename", "{track}-{stem}.{ext}"
                   ])
    cmdline.append(filename)
    # Execute the command if we don't already have output
    stdout = ""
    stderr = ""
    if Tasks.STEM.value in status and State.COMP.value in status[Tasks.STEM.value] and "stdout" in status[Tasks.STEM.value][State.COMP.value]:
        stdout=status[Tasks.STEM.value][State.COMP.value]["stdout"]
        stderr=status[Tasks.STEM.value][State.COMP.value]["stderr"]
    if not os.path.exists(f"{outbase}-{stems[0]}.wav"):
        # Connect stdin to prevent hang when in background
        process = subprocess.Popen(cmdline,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        process.stdin.write("\n\n\n\n\n")
        # Get the first line of output to extract the total number of models to run
        line = process.stdout.readline()
        stdout += line
        p = re.compile('.*bag of ([\d]+) models')
        m = p.match(line)
        models_total = int(m.group(1))
        models_done = 0
        model_done = False
        total_percent = 0
        helpers.setprogress(status['id'], Tasks.STEM, 0)
        while True:
            line = process.stderr.readline()
            stderr += line
            p = re.compile('[\s]*([\d]+)%')
            m = p.match(line)
            if m is not None:
                model_percent = int(m.group(1))
                if model_percent == 100:
                    model_done = True
                if model_percent != 100 and model_done == True:
                    model_done = False
                    models_done += 1
                total_percent = (model_percent / models_total) + (models_done * (100 / models_total))
                helpers.setprogress(status['id'], Tasks.STEM, total_percent)
            if process.poll() is not None:
                for line in process.stdout.readlines():
                    stdout += line
                for line in process.stderr.readlines():
                    stderr += line
                helpers.setprogress(status['id'], Tasks.STEM, 100)
                break

    # Build the dict to return to caller
    ret = { "model": model, "command": { "stdout": stdout, "stderr": stderr } }
    ret[model] = {}
    for stem in stems:
        ret[model][stem] = f"{outbase}-{stem}.wav"
    return ret
