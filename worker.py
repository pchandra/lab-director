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
from config import CONFIG as conf

ROUTER_ADDR = conf['ROUTER_ADDR']
ROUTER_PORT = conf['ROUTER_BACKEND_PORT']

# Only run tasks from the following list on this worker node
ACCEPTABLE_WORK = [ x.value for x in Tasks ]
#ACCEPTABLE_WORK = [ Tasks.MAST.value ]
#ACCEPTABLE_WORK = [ Tasks.ORIG.value, Tasks.WTRM.value, 
#                    Tasks.MAST.value, Tasks.KBPM.value,
#                    Tasks.STEM.value, Tasks.INST.value,
#                    Tasks.LYRC.value, Tasks.MIDI.value,
#                    Tasks.COVR.value, Tasks.STAT.value
#                  ]

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.REQ)
receiver.connect(f"tcp://{ROUTER_ADDR}:{ROUTER_PORT}")

pid = os.getpid()

# Logging helper
def _log(str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stdout.write(f"[{timestamp}] [Worker-{pid}] {str}\n")
    sys.stdout.flush()

# Check if a different task is finished
def _check_ready(file_id, status, dep):
    if status[dep.value]['status'] != State.COMP.value:
        # Throttle this since we might be waiting a while
        time.sleep(1)
        return False
    else:
        return True

# Put a waiting task back in the queue
def _requeue(file_id, task, mark_waiting=True):
    _log(f"Requeuing, task \"{task}\" for {file_id}")
    if mark_waiting:
        api.mark_waiting(file_id, task)
    api.requeue(file_id, task)

def _log_waiting(file_id, task, dep):
    _log(f"Task \"{task}\" for {file_id} is waiting on \"{dep.value}\"")

def _run(file_id, task_type, status, force=False):
    api.mark_inprogress(file_id, task_type.value)
    start = time.time()
    ret = tasks.execute[task_type](file_id, status, force=force)
    stop = time.time()

    # Check if this was short-circuited (task detected it had already run on 'file_id')
    data = None
    if ret is None:
        _log(f"Task \"{task_type.value}\" reports already done for {file_id}")
    else:
        ret['perf'] = {}
        ret['perf']['start'] = datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
        ret['perf']['stop'] = datetime.fromtimestamp(stop).strftime('%Y-%m-%d %H:%M:%S')
        ret['perf']['time_start'] = start
        ret['perf']['time_stop'] = stop
        ret['perf']['time_elapsed'] = stop - start
        data = json.dumps(ret).encode('ascii')
        _log(f"Task \"{task_type.value}\" completed executing for {file_id}")
    api.mark_complete(file_id, task_type.value, data)

def _is_finished(file_id, task_type, status):
    finished_states = [ x.value for x in [ State.COMP, State.FAIL, State.NA ] ]
    return status[task_type.value]['status'] in finished_states

def _acceptable_work(task):
    return task.lower() in ACCEPTABLE_WORK

def main():
    # Process tasks forever
    _log("Starting up worker with PID: %d" % pid)
    while True:
        # Send 'ready' and ACCEPTABLE_WORK then await a task assignment
        _log("Ready to accept new tasks")
        receiver.send(b"ready " + ' '.join(ACCEPTABLE_WORK).encode('ascii'))
        message = receiver.recv_string()
        _log("Got task: %s" % message)
        tokens = message.split()
        task = tokens[0]
        file_id = tokens[1]

        # Detect if we're supposed to stop
        if task == "stop":
            break

        # Detect if we got a no-op
        if task == "noop":
            time.sleep(1)
            continue

        # If this node shouldn't do the task, sleep for a second and requeue it
        if not _acceptable_work(task):
            _log(f"Not processing tasks of type \"{task}\" on this worker")
            time.sleep(1)
            _requeue(file_id, task, mark_waiting=False)
            continue

        # Get the status for this file and validate the file_id we received
        status = api.get_status(file_id)
        if api.get_beat_info(file_id) is None:
            _log(f"No such id known: {file_id}")
            continue

        # Don't force run anything by default unless the task is in ALL CAPS
        force = False
        if any(x for x in Tasks if x.value.upper() == task):
            force = True
            _log("Forced command: %s" % task)
            task = task.lower()

        # Check that the task is legit before proceeding
        if not any(x for x in Tasks if x.value == task):
            _log("COMMAND NOT RECOGNIZED")
            continue

        # Store an original in the file store
        if task == Tasks.ORIG.value:
            _run(file_id, Tasks.ORIG, status, force)

        # Watermarking original file
        elif task == Tasks.WTRM.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.WTRM, status, force)
            else:
                _log_waiting(file_id, task, Tasks.MAST)
                _requeue(file_id, task)

        # Key and BPM detection
        elif task == Tasks.KBPM.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.KBPM, status, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task)

        # Stem separation
        elif task == Tasks.STEM.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.STEM, status, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task)

        # Track mastering
        elif task == Tasks.MAST.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.MAST, status, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task)

        # Instrumental track from stems
        elif task == Tasks.INST.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.INST, status, force)
            else:
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task)

        # Lyrics from vocals
        elif task == Tasks.LYRC.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.LYRC, status, force)
            else:
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task)

        # MIDI track from stems
        elif task == Tasks.MIDI.value:
            api.mark_notavailable(file_id, task)

        # Cover art generation
        elif task == Tasks.COVR.value:
            api.mark_notavailable(file_id, task)

        # Save the status as a last step
        elif task == Tasks.STAT.value:
            all_done = True
            for t in Tasks:
                if t == Tasks.STAT:
                    continue
                if not _is_finished(file_id, t, status):
                    all_done = False
                    _log_waiting(file_id, task, t)
                    _requeue(file_id, task)
                    break
            if all_done:
                _run(file_id, Tasks.STAT, status, force)

if __name__ == "__main__":
    main()
