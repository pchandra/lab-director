import sys
import time
from datetime import datetime
import zmq
from urllib.request import urlopen
import json
from log import Logger
from taskdef import *
import taskapi as api
import tasks
from config import CONFIG as conf

ROUTER_ADDR = conf['ROUTER_ADDR']
ROUTER_PORT = conf['ROUTER_BACKEND_PORT']
ACCEPTABLE_WORK = conf['ACCEPTABLE_WORK']

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.REQ)
receiver.connect(f"tcp://{ROUTER_ADDR}:{ROUTER_PORT}")

# Get Logger instance
log = Logger('worker')

# Check if a different task is finished
def _check_ready(file_id, status, dep):
    if status[dep.value]['status'] != TaskState.COMP.value:
        # Throttle this since we might be waiting a while
        time.sleep(1)
        return False
    else:
        return True

# Check if a task has failed
def _check_failed(file_id, status, dep):
    if status[dep.value]['status'] == TaskState.FAIL.value:
        return True
    else:
        return False

# Put a waiting task back in the queue
def _requeue(file_id, task, mark_waiting=True):
    log.info(f"Requeuing, task \"{task}\" for {file_id}")
    if mark_waiting:
        api.mark_waiting(file_id, task.lower())
    api.requeue(file_id, task)

def _log_waiting(file_id, task, dep):
    log.info(f"Task \"{task}\" for {file_id} is waiting on \"{dep.value}\"")

def _run(file_id, task_type, force=False):
    api.mark_inprogress(file_id, task_type.value)
    success, ret = False, {}
    with tasks.helpers.TaskGuard(file_id) as tg:
        success, ret = tasks.execute[task_type](tg, force=force)
    # Add the performance data and encode
    ret['perf'] = tg.get_perf()
    data = json.dumps(ret).encode('ascii')
    if not success:
        log.warn(f"Task \"{task_type.value}\" FAILED for {file_id}")
        api.mark_failed(file_id, task_type.value, data)
    else:
        log.info(f"Task \"{task_type.value}\" succeeded for {file_id}")
        api.mark_complete(file_id, task_type.value, data)

def _is_finished(file_id, status, task_type):
    finished_states = [ x.value for x in [ TaskState.COMP, TaskState.FAIL, TaskState.NA ] ]
    return status[task_type.value]['status'] in finished_states

def _acceptable_work(task):
    return task.lower() in ACCEPTABLE_WORK

def main():
    # Process tasks forever
    log.info("Starting up worker")

    # Get an ID for this instance
    try:
        url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
        response = urlopen(url)
        instance_data = json.loads(response.read())
        instance_id = instance_data["instanceId"]
    except:
        import socket
        instance_id = socket.gethostname()

    # Read protocol version string
    with open('version-token') as f:
        proto_ver = f.read().strip()

    while True:
        # Send 'ready' and ACCEPTABLE_WORK then await a task assignment
        log.info("Ready to accept new tasks")
        receiver.send(f"ready {proto_ver} {instance_id} ".encode('ascii') + ' '.join(ACCEPTABLE_WORK).encode('ascii'))
        message = receiver.recv_string()
        log.info("Got task: %s" % message)
        tokens = message.split()
        task = tokens[0]
        file_id = tokens[1]

        # Detect if we're supposed to stop
        if task == "stop":
            log.warn("Stopping worker...")
            break

        # Detect if we got a no-op
        if task == "noop":
            log.warn("No-op received, sleeping 5 seconds")
            time.sleep(5)
            continue

        # If this node shouldn't do the task, sleep for a second and requeue it
        if not _acceptable_work(task):
            log.warn(f"Not processing tasks of type \"{task}\" on this worker")
            time.sleep(1)
            _requeue(file_id, task, mark_waiting=False)
            continue

        # If the task is in ALL CAPS, force the task to run
        force = False
        if any(x for x in Tasks if x.value.upper() == task):
            force = True
            log.warn("Forced command: %s" % task)
            task = task.lower()

        # Get the status for this file
        status = api.get_status(file_id)

        # Check that the task is legit before proceeding
        if not any(x for x in Tasks if x.value == task):
            log.warn("COMMAND NOT RECOGNIZED")
            continue

        # Process any on-demand tasks since they fail gracefully
        if task in [ x.value for x in TASKS_ONDEMAND ]:
            # Get the params from status for on-demand tasks
            jid = status['job_id']
            fid = status['file_id']
            success, ret = False, f"On-demand task \"{task}\" FAILED for {file_id}"
            with tasks.helpers.TaskGuard(fid) as tg:
                success, ret = tasks.ondemand[task](tg, status, force=force)
            l = log.info if success else log.warn
            l(msg)
            continue

        # Short-circuit tasks whose main dependency has failed
        if status['type'] == 'beat' and _check_failed(file_id, status, Tasks.ORIG) and task != Tasks.ORIG.value:
            log.info(f"Task \"{task}\" FAILED executing for {file_id}")
            error = { 'message': f"Task {Tasks.ORIG.value} failed", 'failed': True }
            data = json.dumps(error).encode('ascii')
            api.mark_failed(file_id, task, data)
            continue
        if status['type'] == 'song' and _check_failed(file_id, status, Tasks.ORIG) and task != Tasks.ORIG.value:
            log.info(f"Task \"{task}\" FAILED executing for {file_id}")
            error = { 'message': f"Task {Tasks.ORIG.value} failed", 'failed': True }
            data = json.dumps(error).encode('ascii')
            api.mark_failed(file_id, task, data)
            continue
        if status['type'] == 'soundkit' and _check_failed(file_id, status, Tasks.OGSK) and task != Tasks.OGSK.value:
            log.info(f"Task \"{task}\" FAILED executing for {file_id}")
            error = { 'message': f"Task {Tasks.OGSK.value} failed", 'failed': True }
            data = json.dumps(error).encode('ascii')
            api.mark_failed(file_id, task, data)
            continue


        # Analyze an original beat/song in the file store
        if task == Tasks.ORIG.value:
            _run(file_id, Tasks.ORIG, force)

        # Check initial soundkit upload
        elif task == Tasks.OGSK.value:
            _run(file_id, Tasks.OGSK, force)

        # Gather Zip inventory and metadata
        elif task == Tasks.ZINV.value:
            if _check_ready(file_id, status, Tasks.OGSK):
                _run(file_id, Tasks.ZINV, force)
            else:
                _log_waiting(file_id, task, Tasks.OGSK)
                _requeue(file_id, task.upper() if force else task)

        # Create soundkit graphics if there's a preview
        elif task == Tasks.KGFX.value:
            _run(file_id, Tasks.KGFX, force)

        # Bar graphics generation
        elif task == Tasks.BARS.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.BARS, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)

        # Genre autodetection
        elif task == Tasks.GENR.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.GENR, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)

        # Watermarking original file
        elif task == Tasks.WTRM.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.WTRM, force)
            else:
                _log_waiting(file_id, task, Tasks.MAST)
                _requeue(file_id, task.upper() if force else task)

        # Key and BPM detection
        elif task == Tasks.KBPM.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.KBPM, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)

        # Stem separation
        elif task == Tasks.STEM.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.STEM, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)

        # Track mastering
        elif task == Tasks.MAST.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.MAST, force)
            else:
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)

        # Instrumental track from stems
        elif task == Tasks.INST.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.INST, force)
            else:
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task.upper() if force else task)

        # Vocal analysis from stems
        elif task == Tasks.VOCL.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.VOCL, force)
            else:
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task.upper() if force else task)

        # Lyrics from vocals
        elif task == Tasks.LYRC.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.LYRC, force)
            else:
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task.upper() if force else task)

        # Waveform png generation
        elif task == Tasks.WGFX.value:
            if not _check_ready(file_id, status, Tasks.ORIG):
                _log_waiting(file_id, task, Tasks.ORIG)
                _requeue(file_id, task.upper() if force else task)
            elif not _check_ready(file_id, status, Tasks.STEM):
                _log_waiting(file_id, task, Tasks.STEM)
                _requeue(file_id, task.upper() if force else task)
            elif not _check_ready(file_id, status, Tasks.MAST):
                _log_waiting(file_id, task, Tasks.MAST)
                _requeue(file_id, task.upper() if force else task)
            elif not _check_ready(file_id, status, Tasks.INST):
                _log_waiting(file_id, task, Tasks.INST)
                _requeue(file_id, task.upper() if force else task)
            else:
                _run(file_id, Tasks.WGFX, force)

        # MIDI track from stems
        elif task == Tasks.MIDI.value:
            api.mark_notavailable(file_id, task)

        # Save the status as a last step
        elif task == Tasks.STAT.value:
            all_done = True
            to_do = None
            if status['type'] == 'beat':
                to_do = TASKS_BEAT
            elif status['type'] == 'song':
                to_do = TASKS_SONG
            elif status['type'] == 'soundkit':
                to_do = TASKS_SOUNDKIT
            for t in to_do:
                if t == Tasks.STAT:
                    continue
                if not _is_finished(file_id, status, t):
                    all_done = False
                    _log_waiting(file_id, task, t)
                    _requeue(file_id, task.upper() if force else task)
                    break
            if all_done:
                _run(file_id, Tasks.STAT, force)

if __name__ == "__main__":
    main()
