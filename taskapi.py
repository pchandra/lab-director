import time
import json
from urllib.request import urlopen
from taskdef import *
from config import CONFIG as conf

# URL Hosting the director HTTP API (flask)
BASE_URL = f"http://{conf['DIRECTOR_ADDR']}:{conf['DIRECTOR_PORT']}"

def get_status(file_id):
    response = urlopen(BASE_URL + f"/status/{file_id}")
    return json.loads(response.read())

def mark_notavailable(file_id, task):
    urlopen(BASE_URL + f"/update-notavailable/{file_id}/{task}")
    return

def mark_waiting(file_id, task, data=None):
    urlopen(BASE_URL + f"/update-waiting/{file_id}/{task}", data)
    return

def mark_inprogress(file_id, task, data=None):
    urlopen(BASE_URL + f"/update-inprogress/{file_id}/{task}", data)
    return

def mark_complete(file_id, task, data=None):
    urlopen(BASE_URL + f"/update-complete/{file_id}/{task}", data)
    return

def mark_failed(file_id, task, data=None):
    urlopen(BASE_URL + f"/update-failed/{file_id}/{task}", data)
    return

def requeue(file_id, task):
    # Slow it down since we're waiting for something else to finish
    time.sleep(1)
    urlopen(BASE_URL + f"/requeue/{file_id}/{task}")
    return

BEAT_FILE = conf['BATCH_BEAT_FILE]']
SOUNDKIT_FILE = conf['BATCH_SOUNDKIT_FILE]']

_beats = None
_soundkits = None
def _init_old_assetstore():
    global _beats
    global _soundkits
    if _beats is None:
        with open(BEAT_FILE, 'r') as f:
            _beats = json.load(f)
        with open(SOUNDKIT_FILE, 'r') as f:
            _soundkits = json.load(f)

def get_beat_download_url(file_id):
    beat = get_beat_info(file_id)
    if beat is not None:
        ret = [ x['url'] for x in beat['license_rights'][0]['files'] if x['type'] == 'WAV+' ]
        if len(ret) == 1:
            return ret[0]
    return None

def get_beat_info(file_id):
    _init_old_assetstore()
    ret = [ x for x in _beats if x['id'] == file_id ]
    if len(ret) == 1:
        return ret[0]
    return None

def get_soundkit_info(file_id):
    _init_old_assetstore()
    ret = [ x for x in _soundkits if x['id'] == file_id ]
    if len(ret) == 1:
        return ret[0]
    return None
