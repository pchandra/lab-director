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

    ret = {}
    ret['mast'] = filestore.store_file(file_id, master + ".png", f"{Tasks.MAST.value}.png", FILESTORE_PUBLIC)
    ret['orig'] = filestore.store_file(file_id, orig + ".png", f"{Tasks.ORIG.value}.png", FILESTORE_PUBLIC)
    return ret
