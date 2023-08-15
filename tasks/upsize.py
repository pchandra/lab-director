import os
import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

STABLE_DIFFUSION_DIR = conf['STABLE_DIFFUSION_DIR']
ML_DEVICE = conf['ML_DEVICE']

def ondemand(tg, params, force=False):
    key = params['key']
    fmt = params['format']
    job_id = params['job_id']
    if key not in [ f'{Tasks.COVR.value}' ]:
        return False, helpers.msg(f"Key \"{key}\" not recognized")
    if fmt not in [ 'jpg', 'png' ]:
        return False, helpers.msg(f"Format \"{fmt}\" not recognized")
    # Short-circuit if the filestore already has assets we would produce
    tg.add_private([ f"{key}-{Tasks.UPSZ.value}.{fmt}" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.COVR.value}.{fmt}")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.COVR.value}.{fmt}')
    outdir = f"{tg.scratch}/output"
    os.makedirs(outdir, exist_ok=True)
    # Execute the command
    cmdline = []
    cmdline.extend([ "conda", "run",
                     "-n", "ldm",
                     "python3", "optimizedSD/optimized_img2img.py",
                     "--device", ML_DEVICE,
                     "--prompt", "increase resolution",
                     "--skip_grid",
                     "--n_samples", "1",
                     "--n_iter", "1",
                     "--strength", "0.1",
                     "--init-img", filename,
                     "--H", "1500",
                     "--W", "1500",
                     "--turbo",
                     "--format", "png",
                     "--outdir", outdir
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
    ret['input'] = f"{Tasks.COVR.value}.{fmt}"
    outfiles = os.listdir(outdir)
    ret['output'] = tg.put_file(f"{outdir}/{outfiles[0]}", f"{key}-{Tasks.UPSZ.value}.png")
    return True, ret
