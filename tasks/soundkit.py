import os
import re
import magic
import json
from taskdef import *
from . import helpers

def execute(tg, force=False):
    if tg.status['type'] not in [ 'soundkit' ]:
        return False, helpers.msg('Track is not a soundkit')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_private([ f"{Tasks.OGSK.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.OGSK.value}.zip")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.OGSK.value}.zip')

    # Get size and check that it looks like a ZIP
    stats = os.stat(filename)
    size = stats.st_size
    info = magic.from_file(filename)
    p = re.compile('.*[Zz][Ii][Pp].*')
    m = p.match(info)
    if m is None:
        return False, helpers.msg(f'File is not ZIP format')

    ret = {}
    ret['info'] = info
    ret['size'] = size
    tempfile = f"{tg.scratch}/{Tasks.OGSK.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    ret['output'] = tg.put_file(tempfile, f"{Tasks.OGSK.value}.json")
    return True, ret
