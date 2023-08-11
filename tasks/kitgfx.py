from taskdef import *
from . import helpers
from config import CONFIG as conf

def execute(tg, force=False):
    if tg.status['type'] not in [ 'soundkit' ]:
        return False, helpers.msg('Track is not a soundkit')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.WTRM.value}.png",
                    f"{Tasks.WTRM.value}.mp3" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Use the preview, aka 'watermark' to make the graphics
    preview = tg.get_file(f"{Tasks.WTRM.value}.mp3")
    if preview is None:
        return False, helpers.msg(f'Input file not found: {Tasks.WTRM.value}.mp3')

    helpers.make_wave_png(preview)
    ret = {}
    ret['output'] = tg.put_file(preview + ".png", f"{Tasks.WTRM.value}.png")
    return True, ret
