import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

IMAGEMAGICK_BIN = conf['IMAGEMAGICK_BIN']

def ondemand(tg, params, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.OGAW.value}.jpg" ])
    #if not force and tg.check_keys():
    #    return True, helpers.msg('Already done')
    tg.force = True

    # Grab the originally set artwork file
    artwork = tg.get_file(f"original-art")
    if artwork is None:
        return False, helpers.msg(f'Input file not found: original-art')

    outfile = f"{tg.scratch}/{Tasks.OGAW.value}.jpg"

    # Build the command line to run
    cmdline = []
    cmdline.append(IMAGEMAGICK_BIN)
    cmdline.extend([ "-size", "512x512",
                     "-strip",
                     "-quality", "75",
                     artwork,
                     outfile
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()

    ret = {}
    ret['stdout'] = stdout
    ret['output'] = tg.put_file(outfile, f"{Tasks.OGAW.value}.jpg")
    return True, ret
