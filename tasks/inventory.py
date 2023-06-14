import os
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFPROBE_BIN = conf['FFPROBE_BIN']
ZIPLINER_BIN = conf['ZIPLINER_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ZINV.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, public):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, private)
        outfile = scratch + f"/{Tasks.ZINV.value}.json"
    except:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File not found', 'failed': True }

    # Build the command line to run
    cmdline = []
    cmdline.append(ZIPLINER_BIN)
    cmdline.extend([ "-i", filename,
                     "-o", outfile,
                     "-f", FFPROBE_BIN
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()

    # Store the JSON file
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.ZINV.value}.json", public)
    ret = {}
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
