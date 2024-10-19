import uuid
from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'label' ]:
        return False, helpers.msg('ID is not label type')

    fmt = params.get('format', ['wav'])

    # Get the list from label directory
    infofile = tg.get_file(f"{Tasks.LABL.value}.json")
    info = []
    if infofile is not None:
        with open(infofile, 'r') as f:
            info = json.load(f)

    for file in tg.iterate_files():
        if file.key[-3:].lower() in fmt:
            if file.key not in [x["file"] for x in info]:
                item = {"file" : file.key, "id" : str(uuid.uuid4())}
                info.append(item)
            print(f"MATCH")

    print(info)
    return True, {}
