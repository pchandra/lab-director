from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.WTRM.value}.png" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return

    # Use the preview, aka 'watermark' to make the graphics
    try:
        preview = filestore.retrieve_file(file_id, f"{Tasks.WTRM.value}.mp3", scratch, public)
    except:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File not found', 'failed': True }

    helpers.make_wave_png(preview)
    ret = {}
    ret['output'] = filestore.store_file(file_id, preview + ".png", f"{Tasks.WTRM.value}.png", private)

    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return ret
