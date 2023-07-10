import os
import re
import magic
import json
from taskdef import *
from . import helpers
from . import filestore

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ ]
    output_keys = [ f"{Tasks.OGSK.value}.json" ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return

    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File not found', 'failed': True }

    # Get size and check that it looks like a ZIP
    stats = os.stat(filename)
    size = stats.st_size
    info = magic.from_file(filename)
    p = re.compile('.*[Zz][Ii][Pp].*')
    m = p.match(info)
    if m is None:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File is not ZIP format', 'failed': True }

    ret = {}
    ret['info'] = info
    ret['size'] = size
    tempfile = f"{scratch}/{Tasks.OGSK.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    ret['output'] = filestore.store_file(file_id, tempfile, f"{Tasks.OGSK.value}.json", private)

    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return ret


