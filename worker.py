import os
import sys
import time
from datetime import datetime
import shutil
import zmq
from urllib.request import urlopen
import json
from taskdef import *
import taskapi as api
import runtask

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.REQ)
receiver.connect("tcp://localhost:3457")

pid = os.getpid()

# Logging helper
def _log(str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stdout.write(f"[{timestamp}] [Worker-{pid}] {str}\n")
    sys.stdout.flush()

# Check if a different task is finished
def _check_ready(file_id, task, status, dep):
    if status[dep.value]['status'] != State.COMP.value:
        _log(f"Task \"{task}\" is waiting on \"{dep.value}\" for {file_id}... requeuing")
        api.mark_waiting(file_id, task)
        api.requeue(file_id, task)
        # Throttle this since we might be waiting a while
        time.sleep(1)
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

def _run(file_id, task_type, filename, status):
    api.mark_inprogress(file_id, task_type.value)
    start = time.time()
    ret = runtask.execute[task_type](filename, status)
    stop = time.time()
    ret['perf'] = {}
    ret['perf']['start'] = datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
    ret['perf']['stop'] = datetime.fromtimestamp(stop).strftime('%Y-%m-%d %H:%M:%S')
    ret['perf']['time_start'] = start
    ret['perf']['time_stop'] = stop
    ret['perf']['time_elapsed'] = stop - start
    data = json.dumps(ret).encode('ascii')
    _log(f"Task \"{task_type.value}\" is complete for {file_id}")
    api.mark_complete(file_id, task_type.value, data)


# Process tasks forever
_log("Starting up worker with PID: %d" % pid)
while True:
    _log("Ready to accept new tasks")
    receiver.send(b"ready")
    message = receiver.recv_string()
    _log("Got task: %s" % message)
    tokens = message.split()
    task = tokens[0]
    file_id = tokens[1]

    # Get the status for this file first
    status = api.get_status(file_id)

    # Check that the task is legit before proceeding
    if not any(x for x in Tasks if x.value == task):
        _log("COMMAND NOT RECOGNIZED")
        continue

    # Get the file locally for our workload
    filename = _get_as_local_file(file_id, status)

    # Key and BPM detection
    if task == Tasks.KBPM.value:
        _run(file_id, Tasks.KBPM, filename, status)

    # Stem separation
    elif task == Tasks.STEM.value:
        if _check_ready(file_id, task, status, Tasks.KBPM):
            _run(file_id, Tasks.STEM, filename, status)

    # Track mastering
    elif task == Tasks.MAST.value:
        _run(file_id, Tasks.MAST, filename, status)

    # Instrumental track from stems
    elif task == Tasks.INST.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.INST, filename, status)

    # Lyrics from vocals
    elif task == Tasks.LYRC.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.LYRC, filename, status)

    # MIDI track from stems
    elif task == Tasks.MIDI.value:
        api.mark_notavailable(file_id, task)

    # Cover art generation
    elif task == Tasks.COVR.value:
        api.mark_notavailable(file_id, task)
