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
import tasks

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
        _log(f"Requeuing, task \"{task}\" is waiting on \"{dep.value}\" for {file_id}")
        api.mark_waiting(file_id, task)
        api.requeue(file_id, task)
        # Throttle this since we might be waiting a while
        time.sleep(1)
        return False
    else:
        return True

def _run(file_id, task_type, status):
    api.mark_inprogress(file_id, task_type.value)
    start = time.time()
    ret = tasks.execute[task_type](file_id, status)
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
    # Send 'ready' and then await a task assignment
    _log("Ready to accept new tasks")
    receiver.send(b"ready")
    message = receiver.recv_string()
    _log("Got task: %s" % message)
    tokens = message.split()
    task = tokens[0]

    # Detect if we're supposed to stop
    if task == "stop":
        break

    # Get the status for this file first
    file_id = tokens[1]
    status = api.get_status(file_id)

    # Check that the task is legit before proceeding
    if not any(x for x in Tasks if x.value == task):
        _log("COMMAND NOT RECOGNIZED")
        continue

    # Store an original in the file store
    if task == Tasks.ORIG.value:
        _run(file_id, Tasks.ORIG, status)

    # Watermarking original file
    elif task == Tasks.WTRM.value:
        if _check_ready(file_id, task, status, Tasks.ORIG):
            _run(file_id, Tasks.WTRM, status)

    # Key and BPM detection
    elif task == Tasks.KBPM.value:
        if _check_ready(file_id, task, status, Tasks.ORIG):
            _run(file_id, Tasks.KBPM, status)

    # Stem separation
    elif task == Tasks.STEM.value:
        if _check_ready(file_id, task, status, Tasks.ORIG):
            _run(file_id, Tasks.STEM, status)

    # Track mastering
    elif task == Tasks.MAST.value:
        if _check_ready(file_id, task, status, Tasks.ORIG):
            _run(file_id, Tasks.MAST, status)

    # Instrumental track from stems
    elif task == Tasks.INST.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.INST, status)

    # Lyrics from vocals
    elif task == Tasks.LYRC.value:
        if _check_ready(file_id, task, status, Tasks.STEM):
            _run(file_id, Tasks.LYRC, status)

    # MIDI track from stems
    elif task == Tasks.MIDI.value:
        api.mark_notavailable(file_id, task)

    # Cover art generation
    elif task == Tasks.COVR.value:
        api.mark_notavailable(file_id, task)
