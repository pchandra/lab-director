import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

BARTENDER_BIN = conf['BARTENDER_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'soundkit' ]:
        return False, helpers.msg('Track is not a soundkit')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.WTRM.value}.png",
                    f"{Tasks.WTRM.value}.mp3",
                    f"{Tasks.BARS.value}-desktop.png",
                    f"{Tasks.BARS.value}-mobile.png" ])
    #if not force and tg.check_keys():
    #    return True, helpers.msg('Already done')
    tg.force = True

    # Use the preview, aka 'watermark' to make the graphics
    preview = tg.get_file(f"{Tasks.WTRM.value}.mp3")
    if preview is None:
        return False, helpers.msg(f'Input file not found: {Tasks.WTRM.value}.mp3')

    helpers.make_wave_png(preview)
    ret = {}
    ret['output'] = tg.put_file(preview + ".png", f"{Tasks.WTRM.value}.png")

    svgname = tg.scratch + f"/{Tasks.BARS.value}.svg"
    pngname = tg.scratch + f"/{Tasks.BARS.value}.png"

    # Build the command line to run
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", preview,
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
    ret['desktop'] = tg.put_file(pngname, f"{Tasks.BARS.value}-desktop.png")

    # Run it again for the mobile version
    cmdline = []
    cmdline.append(BARTENDER_BIN)
    cmdline.extend([ "-i", preview,
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
