import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

BARTENDER_BIN = conf['BARTENDER_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.BARS.value}-desktop.png",
                    f"{Tasks.BARS.value}-mobile.png" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    # Use the mp3 version of the original to make the graphics
    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.mp3", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')

    svgname = scratch + f"/{Tasks.BARS.value}.svg"
    pngname = scratch + f"/{Tasks.BARS.value}.png"

    # Build the command line to run
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", filename,
                     "-o", svgname,
                     "-p", pngname,
                     "-b", "200",
                     "-s", "2",
                     "-H", "200",
                     "-W", "1600",
                     "-M", "0.8",
                     "-n"
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Save the desktop version
    ret = {}
    ret['desktop'] = filestore.store_file(file_id, pngname, f"{Tasks.BARS.value}-desktop.png", private)

    # Run it again for the mobile version
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", filename,
                     "-o", svgname,
                     "-p", pngname,
                     "-b", "100",
                     "-s", "2",
                     "-H", "100",
                     "-W", "800",
                     "-M", "0.8",
                     "-n"
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Save the mobile version
    ret['mobile'] = filestore.store_file(file_id, pngname, f"{Tasks.BARS.value}-mobile.png", private)

    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
