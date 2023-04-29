import os
import json
import zipfile
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']

def _file_handler(filename):
    basename = os.path.basename(filename)
    if basename.startswith('.'):
        return
    ret = {}
    ext = os.path.splitext(basename)[1]
    if ext in [ ".wav", ".aiff", ".mp3", ".jpg", ".jpeg", ".png", ".gif"]:
        ret = helpers.get_media_info(filename)
    return ret

def _check_dir(subdir, base, info={}, other=[]):
    dirpath = os.path.abspath(subdir)
    for file in os.listdir(dirpath):
        fullpath = os.path.join(dirpath, file)
        if os.path.isdir(fullpath):
            dirinfo, dirother = _check_dir(fullpath, base)
            info.update(dirinfo)
            other.extend(dirother)
        else:
            result = _file_handler(fullpath)
            key = fullpath.replace(base + '/', '')
            if result == {}:
                other.append(key)
            elif result is not None:
                info[key] = result
    return info, other

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ZINV.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, FILESTORE_SOUNDKITS)
    extracted = scratch + f"/{Tasks.OGSK.value}"

    # Extract the zip archive
    with zipfile.ZipFile(filename, "r") as z:
        z.extractall(extracted)

    # Recursively inventory what we found
    extracted = os.path.abspath(extracted)
    zipinfo, others = _check_dir(extracted, extracted)

    # Summarize some data for the whole zip
    summary = {}
    summary['size-compresssed'] = os.path.getsize(filename)
    summary['size-uncompresssed'] = 0
    summary['file-types'] = {}

    for key in zipinfo.keys():
        basename = os.path.basename(key)
        ext = os.path.splitext(basename)[1]
        fmt = zipinfo[key].get('format')
        if fmt is not None:
            summary['size-uncompresssed'] += int(fmt.get('size', 0))
        summary['file-types'][ext] = summary['file-types'].get(ext, 0) + 1

    # Build the object we will save/return
    ret = {}
    ret['summary'] = summary
    ret['files'] = zipinfo
    ret['others'] = others

    tempfile = f"{scratch}/{Tasks.ZINV.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.ZINV.value}.json", FILESTORE_PUBLIC)

    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
