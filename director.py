import zmq
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
TASKS_BEAT = conf['TASKS_BEAT']
TASKS_SONG = conf['TASKS_SONG']
TASKS_SOUNDKIT = conf['TASKS_SOUNDKIT']

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

def _sanity_check(file_id, status, task=None, allow_upper=False):
    if not file_id in status:
        return False, _err_no_file(file_id)
    if task is not None and (not any(x for x in Tasks if x.value == task)) and (allow_upper and not any(x for x in Tasks if x.value.upper() == task)):
        return False, _err_no_task(task)
    return True, ""

def _create_status(file_id, audio_type):
    ret = {}
    ret['id'] = file_id
    ret['type'] = audio_type
    target = None
    if audio_type == 'beat':
        target = TASKS_BEAT
    elif audio_type == 'song':
        target = TASKS_SONG
    elif audio_type == 'soundkit':
        target = TASKS_SOUNDKIT
    for task in [x.value for x in target]:
        ret[task] = {}
        ret[task]['status'] = TaskState.INIT.value
    return ret

@app.route('/')
def index():
    return _msg('AudioLab HTTP API Service')

@app.route('/convert/<file_id>/<key>/<fmt>')
@app.route('/export/<file_id>/<key>/<fmt>')
def export(file_id, key, fmt):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        return _err_no_file(file_id)
    sender.send_string(f"{Tasks.EXPT.value} {file_id} {key} {fmt}")
    return _msg(f"Sent export task: {key} to {fmt} for: {file_id}")

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

@app.route('/load_beat/<file_id>')
def load_beat(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        STATUS[file_id] = _create_status(file_id, 'beat')
    for task in [x.value for x in TASKS_BEAT]:
        sender.send_string(f"{task} {file_id}")
    return _msg(f"Queued all tasks for beat: {file_id}")

@app.route('/load_song/<file_id>')
def load_song(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        STATUS[file_id] = _create_status(file_id, 'song')
    for task in [x.value for x in TASKS_SONG]:
        sender.send_string(f"{task} {file_id}")
    return _msg(f"Queued all tasks for song: {file_id}")

@app.route('/load_soundkit/<file_id>')
def load_soundkit(file_id):
    STATUS = flask_shelve.get_shelve()
    if not file_id in STATUS:
        STATUS[file_id] = _create_status(file_id, 'soundkit')
    for task in [x.value for x in TASKS_SOUNDKIT]:
        sender.send_string(f"{task} {file_id}")
    return _msg(f"Queued all tasks for soundkit: {file_id}")

@app.route('/requeue/<file_id>/<task>')
def requeue_task(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task, allow_upper=True)
    if not ok:
        return msg
    sender.send_string(f"{task} {file_id}")
    return _msg(f"Re-queued task: {task} for: {file_id}")

@app.route('/status/<file_id>')
def file_status(file_id):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS)
    if not ok:
        return msg
    return STATUS[file_id]

@app.route('/update-inprogress/<file_id>/<task>', methods=['GET', 'POST'])
def update_inprogress(file_id, task):
    STATUS = flask_shelve.get_shelve()
    ok, msg = _sanity_check(file_id, STATUS, task)
    if not ok:
        return msg
    current = STATUS[file_id]
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
    app.run(host=conf['DIRECTOR_BIND'], port = conf['DIRECTOR_PORT'])
