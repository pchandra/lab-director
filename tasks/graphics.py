import os
import json
from taskdef import *
from . import helpers
from config import CONFIG as conf

def execute(tg, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.WGFX.value}.json",
                    f"{Tasks.ORIG.value}.png",
                    f"{Tasks.MAST.value}.png" ])
    # Get the stem metadata and add output/public keys
    stem_json = tg.get_file(f"{Tasks.STEM.value}.json")
    if stem_json is None:
        return False, helpers.msg(f'Input file not found: {Tasks.STEM.value}.json')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)
    stems = metadata['stems-core'] + metadata['stems-extra']
    for stem in stems:
        tg.add_public([ f"{os.path.splitext(stem)[0]}.png" ])
    if not metadata['instrumental']:
        tg.add_public([ f"{Tasks.INST.value}.png" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Start with the master to make the graphics
    master = tg.get_file(f"{Tasks.MAST.value}.mp3")
    if master is None:
        return False, helpers.msg(f'Input file not found: {Tasks.MAST.value}.mp3')
    orig = tg.get_file(f"{Tasks.ORIG.value}.mp3")
    if orig is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.mp3')
    factor = helpers.make_wave_png(master)
    helpers.make_wave_png(orig, factor=factor)

    ret = {}
    ret['scaling'] = factor

    try:
        stems = metadata['stems-core'] + metadata['stems-extra']
        for stem in stems:
            filename = tg.get_file(stem)
            helpers.make_wave_png(filename, factor=factor)
            base = os.path.splitext(stem)[0]
            ret[stem] = tg.put_file(filename + ".png", f"{base}.png")

        if not metadata['instrumental']:
            inst = tg.get_file(f"{Tasks.INST.value}.mp3")
            helpers.make_wave_png(inst, factor=factor)
            ret[Tasks.INST.value] = tg.put_file(inst + ".png", f"{Tasks.INST.value}.png")

        ret[Tasks.MAST.value] = tg.put_file(master + ".png", f"{Tasks.MAST.value}.png")
        ret[Tasks.ORIG.value] = tg.put_file(orig + ".png", f"{Tasks.ORIG.value}.png")

        tempfile = f"{tg.scratch}/{Tasks.WGFX.value}.json"
        with open(tempfile, 'w') as f:
            f.write(json.dumps(ret, indent=2))
        tg.put_file(tempfile, f"{Tasks.WGFX.value}.json")
    except:
        return False, helpers.msg(f'Supporting file(s) not found/failed')
    return True, ret
