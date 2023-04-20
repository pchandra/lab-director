import os
import re
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

DEMUCS_BIN = conf['DEMUCS_BIN']
ML_DEVICE = conf['ML_DEVICE']

def _stems_for_model(model):
    stems = [ "bass", "drums", "other", "vocals"]
    if model == "htdemucs_6s":
        stems.append("guitar")
        stems.append("piano")
    return stems

def _run_demucs_model(file_id, filename, scratch, model, progress_start=0, progress_size=100):
    outbase = f"{scratch}/{model}/{os.path.basename(filename)}"
    stems = _stems_for_model(model)

    # Build the command line to run the demucs model
    cmdline = []
    cmdline.append(DEMUCS_BIN)
    cmdline.extend([ "-d", ML_DEVICE,
                     "-n", model,
                     "-o", scratch,
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
    helpers.setprogress(file_id, Tasks.STEM, progress_start)
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
            helpers.setprogress(file_id, Tasks.STEM, progress_start + total_percent/(100/progress_size))
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(file_id, Tasks.STEM, progress_start + 100/(100/progress_size))
            break

    # Build the dict to return to caller
    ret = { "model": model, "command": { "stdout": stdout, "stderr": stderr } }
    ret[model] = {}
    for stem in stems:
        ret[model][stem] = f"{outbase}-{stem}.wav"
    return ret

def _check_stems(demucs, model):
    stems_present = {}
    stems_good = {}
    for stem in demucs[model].keys():
        stemfile = demucs[model][stem]
        totally, mostly = helpers.is_silent(stemfile)
        if not totally:
            stems_present[stem] = stemfile
        if not mostly:
            stems_good[stem] = stemfile
    return stems_present, stems_good

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.STEM.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys):
        return None

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, Tasks.ORIG.value, scratch)
    ret = {}
    # First run the 6 source model
    ret['phase1'] = _run_demucs_model(file_id, filename, scratch, 'htdemucs_6s', progress_size = 50)
    stems_present, stems_good = _check_stems(ret['phase1'], 'htdemucs_6s')

    # If no guitar or piano, run the higher quality 4 source model
    if "guitar" not in stems_good.keys() and "piano" not in stems_good.keys():
        ret['phase2'] = _run_demucs_model(file_id, filename, scratch, 'htdemucs_ft', progress_start = 50, progress_size = 50)
        stems_present, stems_good = _check_stems(ret['phase2'], 'htdemucs_ft')
    else:
        helpers.setprogress(file_id, Tasks.STEM, 100)

    # If no vocals, it's probably instrumental
    ret['instrumental'] = "vocals" not in stems_good.keys()

    # Save each stem back to filestore
    for stem in stems_present.keys():
        stored_location = filestore.store_file(file_id, stems_present[stem], f'{Tasks.STEM.value}-{stem}.wav')
        stems_present[stem] = stored_location

    # Build a metadata dict to save to filestore
    stem_obj = {}
    stem_obj['instrumental'] = ret['instrumental']
    stem_obj['stems-present'] = [ f'{Tasks.STEM.value}-{x}.wav' for x in stems_present.keys() ]
    stem_obj['stems'] = [ f'{Tasks.STEM.value}-{x}.wav' for x in stems_good.keys() ]
    tempfile = f"{scratch}/{Tasks.STEM.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(stem_obj, indent=2))
    filestore.store_file(file_id, tempfile, f"{Tasks.STEM.value}.json")

    ret['output'] = [ {'type':x,'file':stems_present[x]} for x in stems_present.keys()]
    helpers.destroy_scratch_dir(scratch)
    return ret
