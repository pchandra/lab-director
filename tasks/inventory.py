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
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.ZINV.value}.json" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')
    outfile = scratch + f"/{Tasks.ZINV.value}.json"
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
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.ZINV.value}.json", private)
    ret = {}
    ret['output'] = stored_location
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
