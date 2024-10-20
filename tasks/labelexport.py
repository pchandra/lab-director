import uuid
import json
import taskapi as api
from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'label' ]:
        return False, helpers.msg('ID is not label type')

    keys = params.get('keys', [f"{Tasks.RDIO.value}.wav", f"{Tasks.LYRC.value}.txt"])

    # Get the list from label directory
    infofile = tg.get_file(f"{Tasks.LABL.value}.json")
    if infofile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.LABL.value}.json')

    with open(infofile, 'r') as f:
        info = json.load(f)

    # Export files back to original location
    for item in info:
        index = f"{tg.file_id}_{item['id']}"
        for key in keys:
            tg.copy_file(f"{index}/{key}", f"{tg.file_id}/{item['file']}/{key}")

    ret = {}
    ret['items'] = info

    return True, ret
