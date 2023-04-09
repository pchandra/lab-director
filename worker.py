import sys
import time
import zmq
from urllib.request import urlopen
import json
from taskdef import *

context = zmq.Context()

# Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:2346")

BASE_URL = "http://localhost:5000"
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

    # Big switch statement based on task type
    if task == "KEY-BPM":
        _mark_inprogress(file_id, task)
        # Do the work
        time.sleep(30)
        _mark_complete(file_id, task)
    elif task == "STEMS":
        if status['KEY-BPM'] != State.COMP.value:
            _mark_waiting(file_id, task)
            _requeue(file_id, task)
        else:
            _mark_inprogress(file_id, task)
            # Do the work
            time.sleep(30)
            _mark_complete(file_id, task)
    elif task == "MASTERING":
        _mark_inprogress(file_id, task)
        # Do the work
        time.sleep(30)
        _mark_complete(file_id, task)
    elif task == "INSTRUMENTAL":
        if status['STEMS'] != State.COMP.value:
            _mark_waiting(file_id, task)
            _requeue(file_id, task)
        else:
            _mark_inprogress(file_id, task)
            # Do the work
            time.sleep(30)
            _mark_complete(file_id, task)
    elif task == "LYRICS":
        if status['STEMS'] != State.COMP.value:
            _mark_waiting(file_id, task)
            _requeue(file_id, task)
        else:
            _mark_inprogress(file_id, task)
            # Do the work
            time.sleep(30)
            _mark_complete(file_id, task)
    elif task == "MIDI":
        _mark_notavailable(file_id, task)
    elif task == "COVERART":
        _mark_notavailable(file_id, task)
    else:
        sys.stdout.write(f"NOT RECOGNIZED: {message}\n")
        sys.stdout.flush()
