import os
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

ZIPLINER_BIN = conf['ZIPLINER_BIN']
FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ZINV.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, FILESTORE_SOUNDKITS)
    outfile = scratch + f"/{Tasks.ZINV.value}.json"

    # Build the command line to run
    cmdline = []
    cmdline.append(ZIPLINER_BIN)
    cmdline.extend([ "-i", filename,
                     "-o", outfile
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()

    # Store the JSON file
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.ZINV.value}.json", FILESTORE_PUBLIC)
    ret = {}
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
