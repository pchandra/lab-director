import uuid
import json
import taskapi as api
from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'batch' ]:
        return False, helpers.msg('ID is not batch type')

    fmt = params.get('format', ['wav'])
    lyrics = params.get('lyrics', True)
    radio = params.get('radio', True)

    # Get the list from batch directory
    infofile = tg.get_file(f"{Tasks.BTCH.value}.json")
    info = []
    if infofile is not None:
        with open(infofile, 'r') as f:
            info = json.load(f)

    # Setup original to process if not already complete
    for file in tg.iterate_files():
        if file.key[-3:].lower() in fmt:
            if file.key not in [x["file"] for x in info]:
                item_id = str(uuid.uuid4())
                item = {"file" : file.key, "id" : item_id}
                info.append(item)
                index = f"{tg.file_id}_{item_id}"
                tg.copy_file(file.key, f"{index}/{Tasks.ORIG.value}")

    # Run lyrics and radio if requested
    for item in info:
        index = f"{tg.file_id}_{item['id']}"
        api.load_batch_item(index)
        if lyrics:
            api.lyrics(index)
        if radio:
            api.radio(index)

    outfile = f"{tg.scratch}/{Tasks.BTCH.value}.json"
    with open(outfile, 'w') as f:
        f.write(json.dumps(info, indent=2))

    ret = {}
    ret['items'] = info
    ret['outfile'] = tg.put_file(outfile, f"{Tasks.BTCH.value}.json")

    return True, ret
