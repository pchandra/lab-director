import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore

KEYBPM_BIN = '/Users/chandra/ll/co/key-bpm-finder/keymaster-json.py'

def execute(file_id, status):
    filename = filestore.retrieve_file(file_id, status, Tasks.ORIG.value, helpers.WORK_DIR + f"/{status['uuid']}")
    # Build the command line to run
    cmdline = []
    cmdline.append('/usr/local/bin/python3.9')
    cmdline.append(KEYBPM_BIN)
    cmdline.append(filename)
    # Execute the command
    process = subprocess.Popen(cmdline, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    tempfile = helpers.WORK_DIR + f"/{status['uuid']}-{Tasks.KBPM.value}.json"
    with open(tempfile, 'w') as f:
        f.write(stdout)
    stored_location = filestore.store_file(file_id, status, tempfile, f"{Tasks.KBPM.value}.json")
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = json.loads(stdout)
    ret['output'] = stored_location
    return ret
