import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

BARTENDER_BIN = conf['BARTENDER_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'beat', 'song' ]:
        return False, helpers.msg('Track is not a beat or song')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.BARS.value}-desktop.png",
                    f"{Tasks.BARS.value}-mobile.png",
                    f"{Tasks.BARS.value}-data.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Use the mp3 version of the original to make the graphics
    filename = tg.get_file(f"{Tasks.MAST.value}.mp3")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.MAST.value}.mp3')

    svgname = tg.scratch + f"/{Tasks.BARS.value}.svg"
    pngname = tg.scratch + f"/{Tasks.BARS.value}.png"
    jsonname = tg.scratch + f"/{Tasks.BARS.value}.json"

    # Build the command line to run
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", filename,
                     "-o", svgname,
                     "-p", pngname,
                     "-j", jsonname,
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
    ret['desktop'] = tg.put_file(pngname, f"{Tasks.BARS.value}-desktop.png")
    ret['jsondata'] = tg.put_file(jsonname, f"{Tasks.BARS.value}-data.json")

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
    ret['mobile'] = tg.put_file(pngname, f"{Tasks.BARS.value}-mobile.png")
    return True, ret
