from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FILESTORE_PUBLIC = conf['FILESTORE_PUBLIC']
FILESTORE_SOUNDKITS = conf['FILESTORE_SOUNDKITS']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.OGSK.value}.zip" ]
    if not force and filestore.check_keys(file_id, output_keys, FILESTORE_SOUNDKITS):
        return

    # Proceed with running this task
    ret = {}
    scratch = helpers.create_scratch_dir()
    # Get the external file
    local_file = filestore.download_file(api.get_soundkit_file_url(file_id), scratch)

    # XXX: Should do some kind of validation that it's a ZIP

    # Store the original
    ret['soundkit'] = filestore.store_file(file_id, local_file, f"{Tasks.OGSK.value}.zip", FILESTORE_SOUNDKITS)
    return ret
