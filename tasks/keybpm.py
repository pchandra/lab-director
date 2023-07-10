import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

KEYMASTER_BIN = conf['KEYMASTER_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.KBPM.value}.json" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return

    filename = filestore.retrieve_file(file_id, Tasks.ORIG.value, scratch, private)
    # Build the command line to run
    cmdline = []
    cmdline.append(KEYMASTER_BIN)
    cmdline.append(filename)
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Validate and write JSON output to tempfile
    json_obj = json.loads(stdout)
    tempfile = f"{scratch}/{Tasks.KBPM.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(json_obj, indent=2))
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.KBPM.value}.json", private)
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = json.loads(stdout)
    ret['output'] = stored_location
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return ret
