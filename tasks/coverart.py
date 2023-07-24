import os
import subprocess
from taskdef import *
from config import CONFIG as conf

STABLE_DIFFUSION_DIR = conf['STABLE_DIFFUSION_DIR']

def _tag(msg):
    return f"{os.path.basename(__file__)}: {msg}"

def ondemand(tg, params, force=False):
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

    outfiles = os.listdir(tg.scratch)
    for i, file in enumerate([ f"{tg.scratch}/{x}" for x in outfiles ]):
        tg.put_file(file, f"{job_id}/pic{i}.png")
    return True, _tag(f"Finished processing job {job_id} for {tg.file_id}")
