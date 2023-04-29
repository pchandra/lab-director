import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

BARTENDER_BIN = conf['BARTENDER_BIN']
FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_BEATS = conf['FILESTORE_BEATS']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.BARS.value}-desktop.png", f"{Tasks.BARS.value}-mobile.png" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()

    # Use the mp3 version of the original to make the graphics
    filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.mp3", scratch, FILESTORE_BEATS)
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
                     "-n"
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Save the desktop version
    ret = {}
    ret['desktop'] = filestore.store_file(file_id, pngname, f"{Tasks.BARS.value}-desktop.png", FILESTORE_PUBLIC)

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
                     "-n"
                   ])
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Save the mobile version
    ret['mobile'] = filestore.store_file(file_id, pngname, f"{Tasks.BARS.value}-mobile.png", FILESTORE_PUBLIC)

    helpers.destroy_scratch_dir(scratch)
    return ret
