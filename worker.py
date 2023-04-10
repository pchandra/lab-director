import os
import sys
import time
import shutil
import zmq
from urllib.request import urlopen
import json
from taskdef import *
import taskapi as api
import runtask

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:2346")

# Check if a different task is finished
def _check_ready(file_id, task, status, dep):
    if status[dep.value]['status'] != State.COMP.value:
        api.mark_waiting(file_id, task)
        api.requeue(file_id, task)
        return False
    else:
        return True

# XXX: REPLACE THIS with one that grabs an actual file
def _get_as_local_file(file_id, status):
    src = os.environ.get('TESTFILE')
    dst = runtask.WORK_DIR + f"/{status['uuid']}"
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    return dst

def _run(file_id, task_type, filename):
    api.mark_inprogress(file_id, task_type.value)
    ret = runtask.execute[task_type](filename)
    data = json.dumps(ret).encode('ascii')
    api.mark_complete(file_id, task_type.value, data)

# Process tasks forever
while True:
    message = receiver.recv_string()
    tokens = message.split()
    task = tokens[0]
    file_id = tokens[1]

    # Get the status for this file first
    status = api.get_status(file_id)

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
        _run(file_id, Tasks.KBPM, filename)

    # Stem separation
    elif task == Tasks.STEM.value:
        if _check_ready(file_id, task, status, Tasks.KBPM):
            _run(file_id, Tasks.STEM, filename)

    # Track mastering
    elif task == Tasks.MAST.value:
        _run(file_id, Tasks.MAST, filename)

    # Instrumental track from stems
    elif task == Tasks.INST.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.INST, filename)

    # Lyrics from vocals
    elif task == Tasks.LYRC.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.LYRC, filename)

    # MIDI track from stems
    elif task == Tasks.MIDI.value:
        api.mark_notavailable(file_id, task)

    # Cover art generation
    elif task == Tasks.COVR.value:
        api.mark_notavailable(file_id, task)
