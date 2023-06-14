import os
import json
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.WGFX.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, public):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()

    # Start with the master to make the graphics
    master = filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", scratch, private)
    orig = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, private)
    factor = helpers.make_wave_png(master)
    helpers.make_wave_png(orig, factor=factor)

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, public)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    ret = {}

    stems = metadata['stems-core'] + metadata['stems-extra']
    for stem in stems:
        filename = filestore.retrieve_file(file_id, stem, scratch, private)
        helpers.make_wave_png(filename, factor=factor)
        base = os.path.splitext(stem)[0]
        ret[stem] = filestore.store_file(file_id, filename + ".png", f"{base}.png", public)

    if not metadata['instrumental']:
        inst = filestore.retrieve_file(file_id, f"{Tasks.INST.value}.wav", scratch, private)
        helpers.make_wave_png(inst, factor=factor)
        ret[Tasks.INST.value] = filestore.store_file(file_id, inst + ".png", f"{Tasks.INST.value}.png", public)

    ret[Tasks.MAST.value] = filestore.store_file(file_id, master + ".png", f"{Tasks.MAST.value}.png", public)
    ret[Tasks.ORIG.value] = filestore.store_file(file_id, orig + ".png", f"{Tasks.ORIG.value}.png", public)

    tempfile = f"{scratch}/{Tasks.WGFX.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    filestore.store_file(file_id, tempfile, f"{Tasks.WGFX.value}.json", public)

    helpers.destroy_scratch_dir(scratch)
    return ret
