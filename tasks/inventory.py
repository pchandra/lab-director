import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

FFPROBE_BIN = conf['FFPROBE_BIN']
ZIPLINER_BIN = conf['ZIPLINER_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'soundkit' ]:
        return False, helpers.msg('Track is not a soundkit')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.ZINV.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.OGSK.value}.zip")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.OGSK.value}.zip')
    outfile = tg.scratch + f"/{Tasks.ZINV.value}.json"
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
    stored_location = tg.put_file(outfile, f"{Tasks.ZINV.value}.json")
    ret = {}
    ret['output'] = stored_location
    return True, ret
