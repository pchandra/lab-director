from . import helpers
from . import filestore

def execute(file_id, status):
    # Special case call with None to bootstrap
    local_file = filestore.retrieve_file(file_id, status, None, helpers.WORK_DIR + f"/{status['uuid']}")
    stored_location = filestore.store_file(file_id, status, local_file, 'original')
    return { 'output': stored_location }
