import time
import json
from urllib.request import urlopen
from taskdef import *
from config import CONFIG as conf

# URL Hosting the director HTTP API (flask)
BASE_URL = f"http://{conf['DIRECTOR_ADDR']}:{conf['DIRECTOR_PORT']}"

def set_queue(length):
    response = urlopen(BASE_URL + f"/set-queue-length/{length}")
    return json.loads(response.read())

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
