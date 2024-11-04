import zmq
import uuid
import time
from waitress import serve
from paste.translogger import TransLogger
from random import randrange
from flask import request
from flask import Flask
import flask_shelve
from taskdef import *
from config import CONFIG as conf

# Flask config vars
app = Flask(__name__)

# Using a Shelve for persistence of the STATUS dict
app.config['SHELVE_FILENAME'] = conf['DIRECTOR_SHELVE']
flask_shelve.init_app(app)

ROUTER_ADDR = conf['ROUTER_ADDR']
ROUTER_PORT = conf['ROUTER_FRONTEND_PORT']

# Prepare our context and socket to push jobs to workers 
context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.connect(f"tcp://{ROUTER_ADDR}:{ROUTER_PORT}")

def _msg(msg, base={}):
    base['message'] = f"{msg}"
    return base

def _err_no_file(file_id):
    return _msg(f"No such file_id {file_id}"), 400

def _err_no_task(task):
    return _msg(f"No such task {task}"), 400

def _err_bad_request(file_id, task):
    return _msg(f"Not accepting task {task} for {file_id}"), 400

def _sanity_check(file_id, status, task=None, allow_upper=False):
    if not file_id in status:
        return False, _err_no_file(file_id)
    if (task is not None and
        (not any(x for x in Tasks if x.value == task)) and
        (allow_upper and not any(x for x in Tasks if x.value.upper() == task))):
        return False, _err_no_task(task)
    return True, ""

def _create_status(file_id, audio_type):
    ret = {}
    ret['id'] = file_id
    # Hack to have batch items pretend to be beats
    ret['type'] = 'beat' if audio_type == 'batch-item' else audio_type
    ret['watchdog'] = time.time()
    target = []
    if audio_type in [ 'beat', 'batch-item' ]:
        target = TASKS_BEAT
    elif audio_type == 'song':
        target = TASKS_SONG
    elif audio_type == 'soundkit':
        target = TASKS_SOUNDKIT
    elif audio_type == 'artist':
        target = TASKS_ARTIST
    for task in [x.value for x in target]:
        ret[task] = {}
        ret[task]['status'] = TaskState.INIT.value
    return ret

def _create_ondemand(file_id, task, params):
    job_id = str(uuid.uuid4())
    params['file_id'] = file_id
    params['job_id'] = job_id
    params['task'] = task
    params[task] = {}
    params[task]['status'] = TaskState.INIT.value
    return job_id, params

def _init_object(file_id, category, status):
    todo = []
    if category == 'artist':
        todo = TASKS_ARTIST
    elif category == 'beat':
        todo = TASKS_BEAT
    elif category == 'song':
        todo = TASKS_SONG
    elif category == 'soundkit':
        todo = TASKS_SOUNDKIT
    elif category == 'batch-item':
        todo = TASKS_BATCHITEM
    else:
        raise Exception(f"Object type not recognized: {category}")
    status[file_id] = _create_status(file_id, category)
    for task in [x.value for x in todo]:
        sender.send_string(f"{task} {file_id}")

@app.route('/')
def index():
    return _msg('AudioLab HTTP API Service')

@app.route('/convert/<file_id>/<key>/<fmt>')
@app.route('/export/<file_id>/<key>/<fmt>')
@app.route('/export/<file_id>', methods=['POST'])
def export(file_id, key, fmt):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    if request.method == 'GET':
        params = {'key': key, 'format':fmt}
    else:
        params = request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.EXPT.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.EXPT.value} {job_id}")
    return _msg(f"Sent {Tasks.EXPT.value} for: {file_id} with {job_id}", params)

@app.route('/artwork/<file_id>')
def artwork(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    params = {}
    job_id, params = _create_ondemand(file_id, Tasks.OGAW.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.OGAW.value} {job_id}")
    return _msg(f"Sent {Tasks.OGAW.value} for: {file_id} with {job_id}", params)

@app.route('/kitgfx/<file_id>')
def kitgfx(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    params = {}
    job_id, params = _create_ondemand(file_id, Tasks.KGFX.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.KGFX.value} {job_id}")
    return _msg(f"Sent {Tasks.KGFX.value} for: {file_id} with {job_id}", params)

@app.route('/coverart/<file_id>')
@app.route('/coverart/<file_id>/<prompt>')
@app.route('/coverart/<file_id>', methods=['POST'])
def coverart(file_id, prompt="a cool music album cover in any artistic style"):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    if request.method == 'GET':
        params = {'prompt': prompt}
    else:
        params = request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.COVR.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.COVR.value} {job_id}")
    return _msg(f"Sent {Tasks.COVR.value} for: {file_id} with {job_id}", params)

@app.route('/radio/<file_id>')
@app.route('/radio/<file_id>', methods=['POST'])
def radio_edit(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    params = {} if request.method == 'GET' else request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.RDIO.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.RDIO.value} {job_id}")
    return _msg(f"Sent {Tasks.RDIO.value} for: {file_id} with {job_id}", params)

@app.route('/lyrics/<file_id>')
@app.route('/lyrics/<file_id>', methods=['POST'])
def lyrics_generation(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    params = {} if request.method == 'GET' else request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.LYRC.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.LYRC.value} {job_id}")
    return _msg(f"Sent {Tasks.LYRC.value} for: {file_id} with {job_id}", params)

@app.route('/upsize/<file_id>/<key>/<fmt>')
@app.route('/upsize/<file_id>', methods=['POST'])
def upsize(file_id, key, fmt):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    if request.method == 'GET':
        params = {'key': key, 'format':fmt}
    else:
        params = request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.UPSZ.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.UPSZ.value} {job_id}")
    return _msg(f"Sent {Tasks.UPSZ.value} for: {file_id} with {job_id}", params)

@app.route('/batch-process/<file_id>')
@app.route('/batch-process/<file_id>', methods=['POST'])
def batch_processing(file_id):
    STATUS = flask_shelve.get_shelve()
    STATUS[file_id] = _create_status(file_id, 'batch')
    params = {} if request.method == 'GET' else request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.BTCH.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.BTCH.value} {job_id}")
    return _msg(f"Sent {Tasks.BTCH.value} for: {file_id} with {job_id}", params)

@app.route('/batch-export/<file_id>')
@app.route('/batch-export/<file_id>', methods=['POST'])
def batch_export(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    params = {} if request.method == 'GET' else request.get_json(force=True)
    job_id, params = _create_ondemand(file_id, Tasks.BEXP.value, params)
    STATUS[job_id] = params
    sender.send_string(f"{Tasks.BEXP.value} {job_id}")
    return _msg(f"Sent {Tasks.BEXP.value} for: {file_id} with {job_id}", params)

@app.route('/stub_beat/<file_id>')
def stub_beat(file_id):
    STATUS = flask_shelve.get_shelve()
    STATUS[file_id] = _create_status(file_id, 'beat')
    return _msg(f"Status entry created for beat: {file_id}")

@app.route('/stub_song/<file_id>')
def stub_song(file_id):
    STATUS = flask_shelve.get_shelve()
    STATUS[file_id] = _create_status(file_id, 'song')
    return _msg(f"Status entry created for song: {file_id}")

@app.route('/stub_soundkit/<file_id>')
def stub_soundkit(file_id):
    STATUS = flask_shelve.get_shelve()
    STATUS[file_id] = _create_status(file_id, 'soundkit')
    return _msg(f"Status entry created for soundkit: {file_id}")

@app.route('/stub_artist/<file_id>')
def stub_artist(file_id):
    STATUS = flask_shelve.get_shelve()
    STATUS[file_id] = _create_status(file_id, 'artist')
    return _msg(f"Status entry created for artist: {file_id}")

@app.route('/force_load_artist/<file_id>')
def force_load_artist(file_id):
    STATUS = flask_shelve.get_shelve()
    _init_object(file_id, 'artist', STATUS)
    return _msg(f"Forced all tasks for artist: {file_id}")

@app.route('/load_artist/<file_id>')
def load_artist(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        _init_object(file_id, 'artist', STATUS)
        return _msg(f"Queued all tasks for artist: {file_id}")
    else:
        return _msg(f"Already loaded artist: {file_id}")

@app.route('/force_load_beat/<file_id>')
def force_load_beat(file_id):
    STATUS = flask_shelve.get_shelve()
    _init_object(file_id, 'beat', STATUS)
    return _msg(f"Forced all tasks for beat: {file_id}")

@app.route('/load_beat/<file_id>')
def load_beat(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        _init_object(file_id, 'beat', STATUS)
        return _msg(f"Queued all tasks for beat: {file_id}")
    else:
        return _msg(f"Already loaded beat: {file_id}")

@app.route('/force_load_song/<file_id>')
def force_load_song(file_id):
    STATUS = flask_shelve.get_shelve()
    _init_object(file_id, 'song', STATUS)
    return _msg(f"Forced all tasks for song: {file_id}")

@app.route('/load_song/<file_id>')
def load_song(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        _init_object(file_id, 'song', STATUS)
        return _msg(f"Queued all tasks for song: {file_id}")
    else:
        return _msg(f"Already loaded song: {file_id}")

@app.route('/force_load_soundkit/<file_id>')
def force_load_soundkit(file_id):
    STATUS = flask_shelve.get_shelve()
    _init_object(file_id, 'soundkit', STATUS)
    return _msg(f"Forced all tasks for soundkit: {file_id}")

@app.route('/load_soundkit/<file_id>')
def load_soundkit(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        _init_object(file_id, 'soundkit', STATUS)
        return _msg(f"Queued all tasks for soundkit: {file_id}")
    else:
        return _msg(f"Already loaded soundkit: {file_id}")

@app.route('/load_batch_item/<file_id>')
def load_batch_item(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        _init_object(file_id, 'batch-item', STATUS)
        return _msg(f"Queued all tasks for batch-item: {file_id}")
    else:
        return _msg(f"Already loaded batch-item: {file_id}")

@app.route('/requeue/<file_id>/<task>')
def requeue_task(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task, allow_upper=True)
    if not ok:
        return msg
    if ((STATUS[file_id]['type'] != 'beat' or task.lower() not in [x.value for x in TASKS_BEAT]) and
        (STATUS[file_id]['type'] != 'song' or task.lower() not in [x.value for x in TASKS_SONG]) and
        (STATUS[file_id]['type'] != 'soundkit' or task.lower() not in [x.value for x in TASKS_SOUNDKIT])):
        return _err_bad_request(file_id, task)
    if task == Tasks.STAT.value:
        current = time.time()
        if current - STATUS[file_id]['watchdog'] > 1800:
            _init_object(file_id, STATUS[file_id]['type'], STATUS)
            return _msg(f"Re-queue triggered reload: {task} for: {file_id}")
    sender.send_string(f"{task} {file_id}")
    return _msg(f"Re-queued task: {task} for: {file_id}")

@app.route('/requeue-ondemand/<job_id>/<task>')
def requeue_ondemand(job_id, task):
    sender.send_string(f"{task} {job_id}")
    return _msg(f"Re-queued task: {task} for: {job_id}")

@app.route('/status/<file_id>')
def file_status(file_id):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS)
    if not ok:
        return msg
    return STATUS[file_id]

@app.route('/get-cache-info')
def cache_info():
    STATUS = flask_shelve.get_shelve()
    return _msg(f"Total status cache size: {len(STATUS.keys())}")

@app.route('/reset-cache')
def reset_cache():
    STATUS = flask_shelve.get_shelve()
    total = 0
    for k in STATUS.keys():
        del STATUS[k]
        total += 1
    return _msg(f"Reset all item status, cleared: {total}")

@app.route('/get-queue-info', methods=['GET'])
def get_queue_info():
    STATUS = flask_shelve.get_shelve()
    base = {}
    try:
        base = STATUS['queue']
        base['summary'] = STATUS['summary']
    except:
        pass
    return _msg("ok", base=base)

@app.route('/set-queue-info/<length>', methods=['GET', 'POST'])
def set_queue_info(length):
    STATUS = flask_shelve.get_shelve()
    try:
        STATUS['queue'] = { 'length': int(length) }
        if request.method == 'POST':
            STATUS['summary'] = request.get_json(force=True)
        else:
            STATUS['summary'] = {}
    except ValueError:
        return _msg("bad request parameter"), 400
    else:
        return _msg("ok")

@app.route('/update-inprogress/<file_id>/<task>', methods=['GET', 'POST'])
def update_inprogress(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
    current[task] = current.get(task, {})
    current[task]['status'] = TaskState.PROG.value
    if request.method == 'POST':
        current[task][TaskState.PROG.value] = request.get_json(force=True)
    STATUS[file_id] = current
    return _msg("ok")

@app.route('/update-waiting/<file_id>/<task>', methods=['GET', 'POST'])
def update_waiting(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
    current[task]['status'] = TaskState.WAIT.value
    if request.method == 'POST':
        current[task][TaskState.WAIT.value] = request.get_json(force=True)
    STATUS[file_id] = current
    return _msg("ok")

@app.route('/update-complete/<file_id>/<task>', methods=['GET', 'POST'])
def update_complete(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
    current[task]['status'] = TaskState.COMP.value
    if request.method == 'POST':
        current[task][TaskState.COMP.value] = request.get_json(force=True)
    STATUS[file_id] = current
    return _msg("ok")

@app.route('/update-failed/<file_id>/<task>', methods=['GET', 'POST'])
def update_failed(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
    current[task]['status'] = TaskState.FAIL.value
    if request.method == 'POST':
        current[task][TaskState.FAIL.value] = request.get_json(force=True)
    STATUS[file_id] = current
    return _msg("ok")

@app.route('/update-notavailable/<file_id>/<task>')
def update_notavailable(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
    current[task]['status'] = TaskState.NA.value
    STATUS[file_id] = current
    return _msg("ok")

if __name__ == '__main__':
    serve(TransLogger(app, setup_console_handler=False), host=conf['DIRECTOR_BIND'], port=conf['DIRECTOR_PORT'])
