import json
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FILESTORE_BEATS = conf['FILESTORE_BEATS']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.STAT.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_BEATS):
        return

    # Proceed with running this task
    # Write 'status' as json to a local file
    scratch = helpers.create_scratch_dir()
    tempfile = f"{scratch}/{Tasks.STAT.value}.json"
    status = api.get_status(file_id)
    with open(tempfile, 'w') as f:
        f.write(json.dumps(status, indent=2))
    # Store json file
    status = api.get_status(file_id)
    bucket = None
    if status['type'] == 'beat':
        bucket = FILESTORE_BEATS
    elif status['type'] == 'soundkit':
        bucket = FILESTORE_SOUNDKITS
    else:
        raise Exception("Unknown type in COVR!")

    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.STAT.value}.json", bucket)
    ret = {}
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
