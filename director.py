import uuid
import zmq
from random import randrange
from flask import request
from flask import Flask
import flask_shelve
from taskdef import *

# Flask config vars
app = Flask(__name__)

# Using a Shelve for persistence of the STATUS dict
app.config['SHELVE_FILENAME'] = 'persistence'
flask_shelve.init_app(app)

# Prepare our context and socket to push jobs to workers 
context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.bind("tcp://*:2346")

def _msg(msg):
  return { "message": f"{msg}" }

def _err_no_file(file_id):
  return _msg(f"No such file_id {file_id}"), 400

def _err_no_task(task):
    return _msg(f"No such task {task}"), 400

def _sanity_check(file_id, status, task=None):
  if not file_id in status:
    return False, _err_no_file(file_id)
  if task is not None and ( not any(x for x in Tasks if x.value == task) ):
    return False, _err_no_task(task)
  return True, ""

@app.route('/')
def index():
  return _msg('AudioLab HTTP API Service')
  
@app.route('/new/<file_id>')
def new_file(file_id):
  STATUS = flask_shelve.get_shelve()
  if file_id in STATUS:
    return _msg(f"Already have state for {file_id}"), 400
  current = {}
  current['id'] = file_id
  current['uuid'] = str(uuid.uuid4())
  for task in [x.value for x in Tasks]:
    current[task] = {}
    current[task]['status'] = State.INIT.value
    sender.send_string(f"{task} {file_id}")
  STATUS[file_id] = current
  return _msg(f"Sent to Work Queue: {task} {file_id}")

@app.route('/requeue/<file_id>/<task>')
def requeue_task(file_id, task):
  STATUS = flask_shelve.get_shelve()
  ok, msg = _sanity_check(file_id, STATUS, task)
  if not ok:
    return msg
  sender.send_string(f"{task} {file_id}")
  return _msg(f"Sent to Work Queue: {task} {file_id}")

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
  current[task]['status'] = State.PROG.value
  if request.method == 'POST':
    current[task][State.PROG.value] = request.get_json(force=True)
  STATUS[file_id] = current
  return _msg("ok")

@app.route('/update-waiting/<file_id>/<task>', methods=['GET', 'POST'])
def update_waiting(file_id, task):
  STATUS = flask_shelve.get_shelve()
  ok, msg = _sanity_check(file_id, STATUS, task)
  if not ok:
    return msg
  current = STATUS[file_id]
  current[task]['status'] = State.WAIT.value
  if request.method == 'POST':
    current[task][State.WAIT.value] = request.get_json(force=True)
  STATUS[file_id] = current
  return _msg("ok")

@app.route('/update-complete/<file_id>/<task>', methods=['GET', 'POST'])
def update_complete(file_id, task):
  STATUS = flask_shelve.get_shelve()
  ok, msg = _sanity_check(file_id, STATUS, task)
  if not ok:
    return msg
  current = STATUS[file_id]
  current[task]['status'] = State.COMP.value
  if request.method == 'POST':
    current[task][State.COMP.value] = request.get_json(force=True)
  STATUS[file_id] = current
  return _msg("ok")

@app.route('/update-failed/<file_id>/<task>', methods=['GET', 'POST'])
def update_failed(file_id, task):
  STATUS = flask_shelve.get_shelve()
  ok, msg = _sanity_check(file_id, STATUS, task)
  if not ok:
    return msg
  current = STATUS[file_id]
  current[task]['status'] = State.FAIL.value
  if request.method == 'POST':
    current[task][State.FAIL.value] = request.get_json(force=True)
  STATUS[file_id] = current
  return _msg("ok")

@app.route('/update-notavailable/<file_id>/<task>')
def update_notavailable(file_id, task):
  STATUS = flask_shelve.get_shelve()
  ok, msg = _sanity_check(file_id, STATUS, task)
  if not ok:
    return msg
  current = STATUS[file_id]
  current[task]['status'] = State.NA.value
  STATUS[file_id] = current
  return _msg("ok")
