import os
import uuid
import json
import taskapi as api
from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'batch' ]:
        return False, helpers.msg('ID is not batch type')

    keys = params.get('keys', [ f"{Tasks.ORIG.value}.wav" ])

    # Get the list from batch directory
    infofile = tg.get_file(f"{Tasks.BTCH.value}.json")
    if infofile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.BTCH.value}.json')

    with open(infofile, 'r') as f:
        info = json.load(f)

    # Export files back to original location
    for item in info:
        index = f"{tg.file_id}_{item['id']}"
        basename = os.path.splitext(item['file'])[0]
        for key in keys:
            tg.copy_file(f"{index}/{key}", f"---{Tasks.BTCH.value.upper()}/{basename}-{key}")

    ret = {}
    ret['items'] = info

    return True, ret
