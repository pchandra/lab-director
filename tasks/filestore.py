import os
import uuid
import shutil
import requests
import mimetypes
import boto3
import taskapi as api
from config import CONFIG as conf

FILESTORE_BACKEND = conf['FILESTORE_BACKEND']
FILESTORE_DIR = conf['FILESTORE_DIR']
MULTIPART_THRESHOLD = conf['MULTIPART_THRESHOLD']

from boto3.s3.transfer import TransferConfig
s3 = boto3.resource('s3')
config = TransferConfig(multipart_threshold=MULTIPART_THRESHOLD)

# Function to download a file locally from a URL
def download_file(url, directory):
    dst = directory + f"/{str(uuid.uuid4())}"
    if url is None:
        return None
    r = requests.get(url, allow_redirects=True)
    with open(dst, 'wb') as f:
        f.write(r.content)
    return dst

# Store a local file in the filestore under 'key'
def store_file(file_id, path, key, section):
    return _backend['store_file'](file_id, path, key, section)

def _local_store_file(file_id, path, key, section):
    # Create a dir for the file_id if it doesn't exist
    outdir = FILESTORE_DIR + f"/{section}/{file_id}"
    os.makedirs(outdir, exist_ok=True)
    dst = outdir + f"/{key}"
    shutil.copyfile(path, dst)
    return dst

# Store the local asset to the new S3 bucket hierarchy under 'key'
def _s3_store_file(file_id, path, key, section):
    s3path = f"{file_id}/{key}"
    file_mime_type, _ = mimetypes.guess_type(key)
    extra = {'ContentType': file_mime_type} if file_mime_type is not None else None
    s3.Bucket(section).upload_file(Filename=path, Key=s3path, Config=config, ExtraArgs=extra)
    return s3path


# Download the file under 'key' in the filestore to the local filesystem
def retrieve_file(file_id, key, directory, section):
    return _backend['retrieve_file'](file_id, key, directory, section)

def _local_retrieve_file(file_id, key, directory, section):
    src = FILESTORE_DIR + f"/{section}/{file_id}" + f"/{key}"
    dst = directory + f"/{key}"
    shutil.copyfile(src, dst)
    return dst

# Download the file under 'key' from the new S3 bucket hierarchy
def _s3_retrieve_file(file_id, key, directory, section):
    s3path = f"{file_id}/{key}"
    basename = key.split('/')[-1]
    filename = directory + f'/{basename}'
    s3.Object(section, s3path).download_file(filename, Config=config)
    return filename


# Check if a key exists in the filestore
def key_exists(file_id, key, section):
    return _backend['key_exists'](file_id, key, section)

def _local_key_exists(file_id, key, section):
    path = FILESTORE_DIR + f"/{section}/{file_id}" + f"/{key}"
    return os.path.exists(path)

def _s3_key_exists(file_id, key, section):
    path = f"{file_id}/{key}"
    results = s3.meta.client.list_objects_v2(Bucket=section, Prefix=path)
    return 'Contents' in results

# Check if all keys in a list exist in the filestore
def check_keys(file_id, keylist, section):
    ret = True
    for key in keylist:
        if not key_exists(file_id, key, section):
            ret = False
            break
    return ret

_backend_local = {}
_backend_local['store_file'] = _local_store_file
_backend_local['retrieve_file'] = _local_retrieve_file
_backend_local['key_exists'] = _local_key_exists

_backend_s3 = {}
_backend_s3['store_file'] = _s3_store_file
_backend_s3['retrieve_file'] = _s3_retrieve_file
_backend_s3['key_exists'] = _s3_key_exists

_backend = _backend_s3 if FILESTORE_BACKEND == "s3" else _backend_local
