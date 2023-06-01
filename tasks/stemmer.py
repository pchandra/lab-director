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
FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_BEATS = conf['FILESTORE_BEATS']

def _stems_for_model(model):
    stems = [ "bass", "drums", "other", "vocals"]
    if model == "htdemucs_6s":
        stems.append("guitar")
        stems.append("piano")
    return stems

def _run_demucs_model(file_id, filename, scratch, model, progress_start=0, progress_size=100):
    outbase = f"{scratch}/{model}/{os.path.splitext(os.path.basename(filename))[0]}"
    stems = _stems_for_model(model)

    # Get the info for the original file to get the bit depth
    infofile = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.json", scratch, FILESTORE_PUBLIC)
    with open(infofile, 'r') as f:
        info = json.load(f)
    bitdepth = info['streams'][0]['bits_per_sample']

    # Build the command line to run the demucs model
    cmdline = []
    cmdline.append(DEMUCS_BIN)
    cmdline.extend([ "-d", ML_DEVICE,
                     "-n", model,
                     "-o", scratch,
                     "--filename", "{track}-{stem}.{ext}"
                   ])
    if bitdepth == 24:
        cmdline.append("--int24")
    elif bitdepth == 32:
        cmdline.append("--float32")
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
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return None

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, FILESTORE_BEATS)
    ret = {}
    # Run the high quality 4 source model and filter for non-silent
    ret['htdemucs_ft'] = _run_demucs_model(file_id, filename, scratch, 'htdemucs_ft', progress_size = 50)
    stems_core, stems_good = _check_stems(ret['htdemucs_ft'], 'htdemucs_ft')

    # Run the 6 source and see if there's a good guitar or piano stem
    ret['htdemucs_6s'] = _run_demucs_model(file_id, filename, scratch, 'htdemucs_6s', progress_start = 50, progress_size = 50)
    _, stems6g = _check_stems(ret['htdemucs_6s'], 'htdemucs_6s')

    # Done with the tool execution
    helpers.setprogress(file_id, Tasks.STEM, 100)

    # See if there's any good ones in the new sources
    stems_extra = {}
    for stem in [ 'guitar', 'piano' ]:
        if stem in stems6g:
            stems_good[stem] = stems6g[stem]
            stems_extra[stem] = stems6g[stem]

    # If no vocals, it's probably instrumental
    ret['instrumental'] = "vocals" not in stems_good.keys()

    # Save each stem back to filestore
    for stem in stems_core.keys():
        stored_location = filestore.store_file(file_id, stems_core[stem], f'{Tasks.STEM.value}-{stem}.wav', FILESTORE_BEATS)
        stems_core[stem] = stored_location
    for stem in stems_extra.keys():
        stored_location = filestore.store_file(file_id, stems_extra[stem], f'{Tasks.STEM.value}-{stem}.wav', FILESTORE_BEATS)
        stems_extra[stem] = stored_location

    # Build a metadata dict to save to filestore
    stem_obj = {}
    stem_obj['instrumental'] = ret['instrumental']
    stem_obj['stems'] = [ f'{Tasks.STEM.value}-{x}.wav' for x in stems_good.keys() ]
    stem_obj['stems-core'] = [ f'{Tasks.STEM.value}-{x}.wav' for x in stems_core.keys() ]
    stem_obj['stems-extra'] = [ f'{Tasks.STEM.value}-{x}.wav' for x in stems_extra.keys() ]
    tempfile = f"{scratch}/{Tasks.STEM.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(stem_obj, indent=2))
    filestore.store_file(file_id, tempfile, f"{Tasks.STEM.value}.json", FILESTORE_PUBLIC)

    ret['output'] = stem_obj
    helpers.destroy_scratch_dir(scratch)
    return ret
