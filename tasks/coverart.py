import os
import json
import PIL.Image
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

    status = api.get_status(file_id)
    url = None
    if status['type'] == 'beat':
        url = api.get_beat_picture_url(file_id)
    elif status['type'] == 'soundkit':
        url = api.get_soundkit_picture_url(file_id)
    else:
        raise Exception("Unknown type in COVR!")

    # Get the cover art file
    local_file = filestore.download_file(url, scratch)
    imgfile = local_file + ".jpg"
    image = PIL.Image.open(local_file)
    image.save(imgfile)

    ret[Tasks.COVR.value] = None
    if local_file is not None:
        ext = os.path.splitext(url)[1]
        ret[Tasks.COVR.value] = f"{Tasks.COVR.value}-orig{ext}"
        tempfile = f"{scratch}/{Tasks.COVR.value}.json"
        with open(tempfile, 'w') as f:
            f.write(json.dumps(ret, indent=2))
        filestore.store_file(file_id, tempfile, f"{Tasks.COVR.value}.json", FILESTORE_PUBLIC)
        ret[Tasks.COVR.value] = filestore.store_file(file_id, imgfile, f"{Tasks.COVR.value}.jpg", FILESTORE_PUBLIC)
        ret[f"{Tasks.COVR.value}-orig"] = filestore.store_file(file_id, local_file, f"{Tasks.COVR.value}-orig{ext}", FILESTORE_PUBLIC)
    return ret
