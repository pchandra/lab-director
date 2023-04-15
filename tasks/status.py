import json
from taskdef import *
from . import helpers
from . import filestore

def execute(file_id, status):
    # Write 'status' as json to a local file
    tempfile = helpers.WORK_DIR + f"/{status['uuid']}-{Tasks.STAT.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(status, indent=2))
    # Store json file
    stored_location = filestore.store_file(file_id, status, tempfile, f"{Tasks.STAT.value}.json")
    ret = {}
    ret['output'] = stored_location
    return ret
