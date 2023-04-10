import os
import sys
import time
import zmq
from urllib.request import urlopen
import json
from taskdef import *

# Working directory for tools to operate
WORK_DIR = '/tmp'
# URL Hosting the director HTTP API (flask)
BASE_URL = "http://localhost:5000"

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:2346")

def _get_status(file_id):
    response = urlopen(BASE_URL + f"/status/{file_id}")
    return json.loads(response.read())

def _mark_notavailable(file_id, task):
    urlopen(BASE_URL + f"/update-notavailable/{file_id}/{task}")
    return

def _mark_waiting(file_id, task):
    urlopen(BASE_URL + f"/update-waiting/{file_id}/{task}")
    return

def _mark_inprogress(file_id, task):
    urlopen(BASE_URL + f"/update-inprogress/{file_id}/{task}")
    return

def _mark_complete(file_id, task):
    urlopen(BASE_URL + f"/update-complete/{file_id}/{task}")
    return

def _mark_failed(file_id, task):
    urlopen(BASE_URL + f"/update-failed/{file_id}/{task}")
    return

def _requeue(file_id, task):
    # Slow it down since we're waiting for something else to finish
    time.sleep(1)
    urlopen(BASE_URL + f"/requeue/{file_id}/{task}")
    return

# Check if a different task is finished
def _check_ready(file_id, task, status, dep):
    if status[dep.value] != State.COMP.value:
        _mark_waiting(file_id, task)
        _requeue(file_id, task)
        return False
    else:
        return True

import os
import shutil
# XXX: REPLACE THIS with one that grabs an actual file
def _get_as_local_file(file_id, status):
    src = os.environ.get('TESTFILE')
    dst = WORK_DIR + f"/{status['uuid']}"
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    return dst

def _runtask(file_id, task_type, filename):
    _mark_inprogress(file_id, task_type.value)
    RUNTASK[task_type](filename)
    _mark_complete(file_id, task_type.value)

# Process tasks forever
while True:
    message = receiver.recv_string()
    tokens = message.split()
    task = tokens[0]
    file_id = tokens[1]

    # Get the status for this file first
    status = _get_status(file_id)

    # Debug output
    sys.stdout.write(f"**WORKER: {message}\n")
    sys.stdout.flush()

    # Check that the task is legit before proceeding
    if not any(x for x in Tasks if x.value == task):
        sys.stdout.write(f"NOT RECOGNIZED: {message}\n")
        sys.stdout.flush()
        continue

    # Get the file locally for our workload
    filename = _get_as_local_file(file_id, status)

    # Key and BPM detection
    if task == Tasks.KBPM.value:
        _runtask(file_id, Tasks.KBPM, filename)

    # Stem separation
    elif task == Tasks.STEM.value:
        if _check_ready(file_id, task, status, Tasks.KBPM):
            _runtask(file_id, Tasks.STEM, filename)

    # Track mastering
    elif task == Tasks.MAST.value:
        _runtask(file_id, Tasks.MAST, filename)

    # Instrumental track from stems
    elif task == Tasks.INST.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _runtask(file_id, Tasks.INST, filename)

    # Lyrics from vocals
    elif task == Tasks.LYRC.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _runtask(file_id, Tasks.LYRC, filename)

    # MIDI track from stems
    elif task == Tasks.MIDI.value:
        _mark_notavailable(file_id, task)

    # Cover art generation
    elif task == Tasks.COVR.value:
        _mark_notavailable(file_id, task)
