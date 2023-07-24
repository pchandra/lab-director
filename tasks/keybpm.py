import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

KEYMASTER_BIN = conf['KEYMASTER_BIN']

def execute(tg, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.KBPM.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.ORIG.value}.mp3")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.mp3')
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
    tempfile = f"{tg.scratch}/{Tasks.KBPM.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(json_obj, indent=2))
    stored_location = tg.put_file(tempfile, f"{Tasks.KBPM.value}.json")
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = json_obj
    ret['output'] = stored_location
    return True, ret
