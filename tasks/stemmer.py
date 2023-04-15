import os
import re
import subprocess
from taskdef import *
from . import helpers
from . import filestore

DEMUCS_BIN = '/usr/local/bin/demucs'

def _stems_for_model(model):
    stems = [ "bass", "drums", "other", "vocals"]
    if model == "htdemucs_6s":
        stems.append("guitar")
        stems.append("piano")
    return stems

def _run_demucs_model(filename, status, model, progress_start=0, progress_size=100):
    outbase = f"{helpers.WORK_DIR}/{model}/{os.path.basename(filename)}"
    stems = _stems_for_model(model)

    # Build the command line to run the demucs model
    cmdline = []
    cmdline.append(DEMUCS_BIN)
    cmdline.extend([ "-d", "cpu",
                     "-n", model,
                     "-o", helpers.WORK_DIR,
                     "--filename", "{track}-{stem}.{ext}"
                   ])
    cmdline.append(filename)

    # Run it
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    process.stdin.write("\n\n\n\n\n")

    # Variables to accumulate output
    stdout = ""
    stderr = ""

    # Get the first line of output to extract the total number of models to run
    line = process.stdout.readline()
    stdout += line
    p = re.compile('.*bag of ([\d]+) models')
    m = p.match(line)
    models_total = int(m.group(1))
    models_done = 0
    model_done = False
    total_percent = 0
    helpers.setprogress(status['id'], Tasks.STEM, progress_start)
    # Interesting output is in stderr, update percent as we go
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
            helpers.setprogress(status['id'], Tasks.STEM, progress_start + total_percent/(100/progress_size))
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(status['id'], Tasks.STEM, progress_start + 100/(100/progress_size))
            break

    # Build the dict to return to caller
    ret = { "model": model, "command": { "stdout": stdout, "stderr": stderr } }
    ret[model] = {}
    for stem in stems:
        ret[model][stem] = f"{outbase}-{stem}.wav"
    return ret

def _check_stems(demucs, model):
    stems_found = {}
    for stem in demucs[model].keys():
        stemfile = demucs[model][stem]
        if not helpers.is_silent(stemfile):
            stems_found[stem] = stemfile
    return stems_found

def execute(file_id, status):
    filename = filestore.retrieve_file(file_id, status, 'original', helpers.WORK_DIR + f"/{status['uuid']}")
    ret = {}
    # First run the 6 source model
    ret['phase1'] = _run_demucs_model(filename, status, 'htdemucs_6s', progress_size = 50)
    stems_found = _check_stems(ret['phase1'], 'htdemucs_6s')

    # If no vocals, it's probably instrumental
    ret['instrumental'] = "vocals" not in stems_found.keys()

    # If no guitar or piano, run the higher quality 4 source model
    if "guitar" not in stems_found.keys() and "piano" not in stems_found.keys():
        ret['phase2'] = _run_demucs_model(filename, status, 'htdemucs_ft', progress_start = 50, progress_size = 50)
        stems_found = _check_stems(ret['phase2'], 'htdemucs_ft')
    else:
        helpers.setprogress(status['id'], Tasks.STEM, 100)

    # Save each stem back to filestore
    for stem in stems_found.keys():
        stored_location = filestore.store_file(file_id, status, stems_found[stem], f'stem-{stem}.wav')
        stems_found[stem] = stored_location

    ret['output'] = [ {'type':x,'file':stems_found[x]} for x in stems_found.keys()]
    return ret
