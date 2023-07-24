import json
from taskdef import *
import taskapi as api
from . import helpers
from config import CONFIG as conf

def execute(tg, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_private([ f"{Tasks.STAT.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Write 'status' as json to a local file
    tempfile = f"{tg.scratch}/{Tasks.STAT.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(tg.status, indent=2))

    stored_location = tg.put_file(tempfile, f"{Tasks.STAT.value}.json")
    ret = {}
    ret['output'] = stored_location
    return True, ret
