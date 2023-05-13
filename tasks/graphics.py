import os
import json
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_BEATS = conf['FILESTORE_BEATS']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.WGFX.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_PUBLIC):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()

    # Start with the master to make the graphics
    master = filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", scratch, FILESTORE_BEATS)
    orig = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, FILESTORE_BEATS)
    factor = helpers.make_wave_png(master)
    helpers.make_wave_png(orig, factor=factor)

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, FILESTORE_PUBLIC)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    ret = {}

    for stem in metadata['stems']:
        filename = filestore.retrieve_file(file_id, stem, scratch, FILESTORE_BEATS)
        helpers.make_wave_png(filename, factor=factor)
        base = os.path.splitext(stem)[0]
        ret[stem] = filestore.store_file(file_id, filename + ".png", f"{base}.png", FILESTORE_PUBLIC)

    if not metadata['instrumental']:
        inst = filestore.retrieve_file(file_id, f"{Tasks.INST.value}.wav", scratch, FILESTORE_BEATS)
        helpers.make_wave_png(inst, factor=factor)
        ret[Tasks.INST.value] = filestore.store_file(file_id, inst + ".png", f"{Tasks.INST.value}.png", FILESTORE_PUBLIC)

    ret[Tasks.MAST.value] = filestore.store_file(file_id, master + ".png", f"{Tasks.MAST.value}.png", FILESTORE_PUBLIC)
    ret[Tasks.ORIG.value] = filestore.store_file(file_id, orig + ".png", f"{Tasks.ORIG.value}.png", FILESTORE_PUBLIC)

    tempfile = f"{scratch}/{Tasks.WGFX.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    filestore.store_file(file_id, tempfile, f"{Tasks.WGFX.value}.json", FILESTORE_PUBLIC)

    helpers.destroy_scratch_dir(scratch)
    return ret
