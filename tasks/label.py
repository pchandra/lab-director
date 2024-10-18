from taskdef import *
from . import helpers
from config import CONFIG as conf

def ondemand(tg, params, force=False):
    if tg.status['type'] not in [ 'label' ]:
        return False, helpers.msg('ID is not label type')
    for i in tg.iterate_files():
        print(i)

    return True, {}
