import sys
import time
from datetime import datetime
import zmq
from urllib.request import urlopen
import json
import logging
from taskdef import *
import taskapi as api
import tasks
from config import CONFIG as conf

ROUTER_ADDR = conf['ROUTER_ADDR']
ROUTER_PORT = conf['ROUTER_BACKEND_PORT']
ACCEPTABLE_WORK = conf['ACCEPTABLE_WORK']
HEARTBEAT_TIME = conf['HEARTBEAT_TIME']
NOOP_TIME = conf['NOOP_TIME']
LOG_PREFIX = conf['LOG_PREFIX']
LOG_DATEFMT = conf['LOG_DATEFMT']
LOG_LEVEL = conf['LOG_LEVEL']

# Setup ZeroMQ connection to receive tasks from the director
context = zmq.Context()
receiver = context.socket(zmq.REQ)
receiver.connect(f"tcp://{ROUTER_ADDR}:{ROUTER_PORT}")

# Get Logger instance
logging.basicConfig(format=LOG_PREFIX, datefmt=LOG_DATEFMT, level=LOG_LEVEL)
log = logging.getLogger('worker')

# Check if a different task is finished
def _check_ready(file_id, status, dep):
    if status[dep.value]['status'] != TaskState.COMP.value:
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
def _requeue(file_id, task, waiting=None):
    add = ""
    if waiting is not None:
        add = f"waiting on \"{waiting.value}\""
        api.mark_waiting(file_id, task.lower())
    log.info(f"Requeue \"{task}\" for {file_id} {add}")
    api.requeue(file_id, task)

def _run(file_id, task_type, force=False):
    api.mark_inprogress(file_id, task_type.value)
    log.info(f"Running \"{task_type.value}\" for {file_id}")
    success, ret = False, {}
    with tasks.helpers.TaskGuard(file_id, task_type, force) as tg:
        tg.success, ret = tasks.execute[task_type](tg, force=force)
    # Add the performance data and encode
    ret['perf'] = tg.get_perf()
    data = json.dumps(ret).encode('ascii')
    if not tg.success:
        log.warning(f"Failed \"{task_type.value}\" for {file_id}")
        api.mark_failed(file_id, task_type.value, data)
    else:
        log.info(f"Success \"{task_type.value}\" for {file_id}")
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

    # Keep a counter for heartbeat messages
    last_msg = time.time()

    while True:
        # Do time sensitive checks first
        now = time.time()
        logf = log.debug
        if now - last_msg > HEARTBEAT_TIME:
            logf = log.info
            last_msg = now
        logf("Ready")
        # Send 'ready' and ACCEPTABLE_WORK then await a task assignment
        receiver.send(f"ready {proto_ver} {instance_id} ".encode('ascii') + ' '.join(ACCEPTABLE_WORK).encode('ascii'))
        message = receiver.recv_string()
        tokens = message.split()
        task = tokens[0]
        file_id = tokens[1]

        # Detect if we're supposed to stop
        if task == Tasks.STOP.value:
            log.warning("Stop message received from router")
            break

        # Detect if we got a no-op
        if task == Tasks.NOOP.value:
            log.debug(f"No-op received, sleeping {NOOP_TIME} second(s)")
            time.sleep(NOOP_TIME)
            continue
        else:
            log.info(f"Received: \"{task}\" for {file_id}")

        # If this node shouldn't do the task, sleep for a second and requeue it
        if not _acceptable_work(task):
            log.warning(f"Not processing tasks of type \"{task}\" on this worker")
            _requeue(file_id, task)
            continue

        # If the task is in ALL CAPS, force the task to run
        force = False
        if any(x for x in Tasks if x.value.upper() == task):
            force = True
            log.warning("Forced command: %s" % task)
            task = task.lower()

        # Get the status for this file
        status = api.get_status(file_id)

        # Check that the task is legit before proceeding
        if not any(x for x in Tasks if x.value == task):
            log.error("COMMAND NOT RECOGNIZED")
            continue

        # Process any on-demand tasks since they fail gracefully
        if task in [ x.value for x in TASKS_ONDEMAND ]:
            # Get the params from status for on-demand tasks
            jid = status['job_id']
            fid = status['file_id']
            api.mark_inprogress(jid, task)
            success, ret = False, {}
            with tasks.helpers.TaskGuard(fid, task) as tg:
                tg.success, ret = tasks.ondemand[task](tg, status, force=force)
            ret['perf'] = tg.get_perf()
            data = json.dumps(ret).encode('ascii')
            if not tg.success:
                log.warning(f"Failed \"{task}\" for {jid} on {fid}")
                api.mark_failed(jid, task, data)
            else:
                log.info(f"Success \"{task}\" for {jid} on {fid}")
                api.mark_complete(jid, task, data)
            continue

        # Short-circuit tasks whose main dependency has failed
        if status['type'] == 'beat' and _check_failed(file_id, status, Tasks.ORIG) and task != Tasks.ORIG.value:
            log.warning(f"Failed \"{task}\" for {file_id}")
            error = { 'message': f"Task {Tasks.ORIG.value} failed", 'failed': True }
            data = json.dumps(error).encode('ascii')
            api.mark_failed(file_id, task, data)
            continue
        if status['type'] == 'song' and _check_failed(file_id, status, Tasks.ORIG) and task != Tasks.ORIG.value:
            log.warning(f"Failed \"{task}\" for {file_id}")
            error = { 'message': f"Task {Tasks.ORIG.value} failed", 'failed': True }
            data = json.dumps(error).encode('ascii')
            api.mark_failed(file_id, task, data)
            continue
        if status['type'] == 'soundkit' and _check_failed(file_id, status, Tasks.OGSK) and task != Tasks.OGSK.value:
            log.warning(f"Failed \"{task}\" for {file_id}")
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
                _requeue(file_id, task.upper() if force else task, Tasks.OGSK)

        # Create soundkit graphics if there's a preview
        elif task == Tasks.KGFX.value:
            _run(file_id, Tasks.KGFX, force)

        # Bar graphics generation
        elif task == Tasks.BARS.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.BARS, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)

        # Genre autodetection
        elif task == Tasks.GENR.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.GENR, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)

        # Watermarking original file
        elif task == Tasks.WTRM.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.WTRM, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)

        # Key and BPM detection
        elif task == Tasks.KBPM.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.KBPM, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)

        # Stem separation
        elif task == Tasks.STEM.value:
            if _check_ready(file_id, status, Tasks.MAST):
                _run(file_id, Tasks.STEM, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)

        # Track mastering
        elif task == Tasks.MAST.value:
            if _check_ready(file_id, status, Tasks.ORIG):
                _run(file_id, Tasks.MAST, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.ORIG)

        # Instrumental track from stems
        elif task == Tasks.INST.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.INST, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.STEM)

        # Vocal analysis from stems
        elif task == Tasks.VOCL.value:
            if _check_ready(file_id, status, Tasks.STEM):
                _run(file_id, Tasks.VOCL, force)
            else:
                _requeue(file_id, task.upper() if force else task, Tasks.STEM)

        # Waveform generation
        elif task == Tasks.WGFX.value:
            if not _check_ready(file_id, status, Tasks.ORIG):
                _requeue(file_id, task.upper() if force else task, Tasks.ORIG)
            elif not _check_ready(file_id, status, Tasks.STEM):
                _requeue(file_id, task.upper() if force else task, Tasks.STEM)
            elif not _check_ready(file_id, status, Tasks.MAST):
                _requeue(file_id, task.upper() if force else task, Tasks.MAST)
            elif (not _check_ready(file_id, status, Tasks.INST) and
                  not _check_failed(file_id, status, Tasks.INST)):
                _requeue(file_id, task.upper() if force else task, Tasks.INST)
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
                    _requeue(file_id, task.upper() if force else task, t)
                    break
            if all_done:
                _run(file_id, Tasks.STAT, force)

if __name__ == "__main__":
    main()
