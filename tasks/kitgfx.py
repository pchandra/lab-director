from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.WTRM.value}.png" ]
    if not force and filestore.check_keys(file_id, output_keys, public):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()

    # Use the preview, aka 'watermark' to make the graphics
    try:
        preview = filestore.retrieve_file(file_id, f"{Tasks.WTRM.value}.mp3", scratch, public)
    except:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File not found', 'failed': True }

    helpers.make_wave_png(preview)
    ret = {}
    ret['output'] = filestore.store_file(file_id, preview + ".png", f"{Tasks.WTRM.value}.png", public)

    helpers.destroy_scratch_dir(scratch)
    return ret
