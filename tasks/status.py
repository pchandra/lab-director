import json
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.STAT.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, private):
        return

    # Proceed with running this task
    # Write 'status' as json to a local file
    scratch = helpers.create_scratch_dir()
    tempfile = f"{scratch}/{Tasks.STAT.value}.json"
    status = api.get_status(file_id)
    with open(tempfile, 'w') as f:
        f.write(json.dumps(status, indent=2))

    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.STAT.value}.json", private)
    ret = {}
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
