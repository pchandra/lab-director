import os
import json
import subprocess
from taskdef import *
from config import CONFIG as conf

STABLE_DIFFUSION_DIR = conf['STABLE_DIFFUSION_DIR']

def ondemand(tg, params, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_private([ f"{Tasks.COVR.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    prompt = params['prompt']
    job_id = params['job_id']
    # Execute the command
    cmdline = []
    cmdline.extend([ "conda", "run",
                     "-n", "ldm",
                     "python3", "optimizedSD/optimized_txt2img.py",
                     "--prompt", prompt,
                     "--ckpt", "sd-v1-4.ckpt",
                     "--skip_grid",
                     "--n_samples", "4",
                     "--n_iter", "1",
                     "--H", "512",
                     "--W", "512",
                     "--turbo",
                     "--outdir", tg.scratch
                   ])
    process = subprocess.Popen(cmdline,
                               cwd=STABLE_DIFFUSION_DIR,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret['files'] = []
    outfiles = os.listdir(tg.scratch)
    for i, file in enumerate([ f"{tg.scratch}/{x}" for x in outfiles ]):
        f = tg.put_file(file, f"{Tasks.COVR.value}/pic{i}.png")
        ret['files'].append(f)
    tempfile = f"{tg.scratch}/{Tasks.COVR.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(params, indent=2))
    ret['output'] = tg.put_file(tempfile, f"{Tasks.COVR.value}.json")
    return True, ret
