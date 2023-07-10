import os
import json
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.WGFX.value}.json",
                    f"{Tasks.ORIG.value}.png",
                    f"{Tasks.MAST.value}.png" ]
    # Get the stem metadata and add output/public keys
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, private)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)
    stems = metadata['stems-core'] + metadata['stems-extra']
    for stem in stems:
        public_keys.append(f"{os.path.splitext(stem)[0]}.png")
    if not metadata['instrumental']:
        public_keys.append(f"{Tasks.INST.value}.png")
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    # Start with the master to make the graphics
    try:
        master = filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", scratch, private)
        orig = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')
    factor = helpers.make_wave_png(master)
    helpers.make_wave_png(orig, factor=factor)

    ret = {}
    ret['scaling'] = factor

    stems = metadata['stems-core'] + metadata['stems-extra']
    for stem in stems:
        filename = filestore.retrieve_file(file_id, stem, scratch, private)
        helpers.make_wave_png(filename, factor=factor)
        base = os.path.splitext(stem)[0]
        ret[stem] = filestore.store_file(file_id, filename + ".png", f"{base}.png", private)

    if not metadata['instrumental']:
        inst = filestore.retrieve_file(file_id, f"{Tasks.INST.value}.wav", scratch, private)
        helpers.make_wave_png(inst, factor=factor)
        ret[Tasks.INST.value] = filestore.store_file(file_id, inst + ".png", f"{Tasks.INST.value}.png", private)

    ret[Tasks.MAST.value] = filestore.store_file(file_id, master + ".png", f"{Tasks.MAST.value}.png", private)
    ret[Tasks.ORIG.value] = filestore.store_file(file_id, orig + ".png", f"{Tasks.ORIG.value}.png", private)

    tempfile = f"{scratch}/{Tasks.WGFX.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(ret, indent=2))
    filestore.store_file(file_id, tempfile, f"{Tasks.WGFX.value}.json", private)

    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
