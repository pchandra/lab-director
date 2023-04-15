import os
import shutil


FILESTORE_BACKEND="local"
FILESTORE_DIR = '/tmp/STORE'


# Function to bootstrap things by grabbing an asset from off-site and downloading it locally
def get_external_file(file_id, status, directory):
    return _backend['get_external_file'](file_id, status, directory)

def _local_get_external_file(file_id, status, directory):
    src = os.environ.get('TESTFILE')
    dst = directory + f"/{status['uuid']}"
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    return dst

# XXX: This will be the function to get the file_id URL from site API and grab file from old S3 bucket
def _s3_get_external_file(file_id, status, directory):
    return ""


# Store a local file in the filestore under 'key'
def store_file(file_id, status, path, key):
    return _backend['store_file'](file_id, status, path, key)

def _local_store_file(file_id, status, path, key):
    # Create a dir for the file_id if it doesn't exist
    outdir = FILESTORE_DIR + f"/{file_id}"
    os.makedirs(outdir, exist_ok=True)
    dst = outdir + f"/{key}"
    shutil.copyfile(path, dst)
    return dst

# XXX: This will be the function to store the local asset to the new S3 bucket hierarchy under 'key'
def _s3_store_file(file_id, status, path, key):
    pass


# Download the file under 'key' in the filestore to the local filesystem
def retrieve_file(file_id, status, key, directory):
    return _backend['retrieve_file'](file_id, status, key, directory)

def _local_retrieve_file(file_id, status, key, directory):
    os.makedirs(directory, exist_ok=True)
    if key is None:
        return get_external_file(file_id, status, directory)
    src = FILESTORE_DIR + f"/{file_id}" + f"/{key}"
    dst = directory + f"/{key}"
    shutil.copyfile(src, dst)
    return dst

# XXX: This will be the function to grab an asset (under 'key') from the new S3 bucket hierarchy
def _s3_retrieve_file(file_id, status, key, directory):
    pass


# Check if a key exists in the filestore
def key_exists(file_id, status, key):
    return _backend['key_exists'](file_id, status, key)

def _local_key_exists(file_id, status, key):
    path = FILESTORE_DIR + f"/{file_id}" + f"/{key}"
    return os.path.exists(path)

def _s3_key_exists(file_id, status, key):
    pass


# Check if all keys in a list exist in the filestore
def check_keys(file_id, status, keylist):
    ret = True
    for key in keylist:
        if not key_exists(file_id, status, key):
            ret = False
            break
    return ret

_backend_local = {}
_backend_local['store_file'] = _local_store_file
_backend_local['retrieve_file'] = _local_retrieve_file
_backend_local['key_exists'] = _local_key_exists
_backend_local['get_external_file'] = _local_get_external_file

_backend_s3 = {}
_backend_s3['store_file'] = _s3_store_file
_backend_s3['retrieve_file'] = _s3_retrieve_file
_backend_s3['key_exists'] = _s3_key_exists
_backend_s3['get_external_file'] = _s3_get_external_file

_backend = _backend_s3 if FILESTORE_BACKEND == "s3" else _backend_local
