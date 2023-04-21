import os
import re
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
PHASELIMITER_BIN = conf['PHASELIMITER_BIN']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.MAST.value}.wav" ]
    if not force and filestore.check_keys(file_id, output_keys):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch)
    outfile = f"{scratch}/{Tasks.MAST.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(PHASELIMITER_BIN)
    cmdline.extend([ "-reference", "-9",
                     "-reference_mode", "loudness",
                     "-ceiling_mode", "lowpass_true_peak",
                     "-ceiling", "-0.5",
                     "-mastering_mode", "mastering5",
                     "mastering5_mastering_level", "0.7",
                     "-input", filename,
                     "-output", outfile
                   ])

    # Connect stdin to prevent hang when in background
    stdout = ""
    stderr = ""
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    process.stdin.write("\n\n\n\n\n")

    percent = 0
    helpers.setprogress(file_id, Tasks.MAST, 0)
    while True:
        line = process.stdout.readline()
        stdout += line
        p = re.compile('progression: ([\d.]+)')
        m = p.match(line)
        if m is not None:
            percent = float(m.group(1)) * 100
            helpers.setprogress(file_id, Tasks.MAST, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(file_id, Tasks.MAST, 100)
            break

    # Store the resulting file
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.MAST.value}.wav")

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
