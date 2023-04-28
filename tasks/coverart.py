import os
import json
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.COVR.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return

    # Proceed with running this task
    ret = {}
    scratch = helpers.create_scratch_dir()

    # Get the cover art file
    local_file = filestore.get_beat_picture(file_id, scratch)

    ret[Tasks.COVR.value] = None
    if local_file is not None:
        ext = os.path.splitext(api.get_beat_picture_url(file_id))[1]
        ret[Tasks.COVR.value] = f"{Tasks.COVR.value}{ext}"
        tempfile = f"{scratch}/{Tasks.COVR.value}.json"
        with open(tempfile, 'w') as f:
            f.write(json.dumps(ret, indent=2))
        filestore.store_file(file_id, tempfile, f"{Tasks.COVR.value}.json", FILESTORE_PUBLIC)
        ret[Tasks.COVR.value] = filestore.store_file(file_id, local_file, f"{Tasks.COVR.value}{ext}", FILESTORE_PUBLIC)
    return ret
