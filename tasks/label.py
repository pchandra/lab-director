from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'label' ]:
        return False, helpers.msg('ID is not label type')

    fmt = params.get('format', ['wav'])

    for i in tg.iterate_files():
        print(i.key)
        if i.key[-3:].lower() in fmt:
            print(f"MATCH")

    return True, {}
