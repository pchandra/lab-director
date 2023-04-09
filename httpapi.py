import zmq
from random import randrange
from flask import Flask
import flask_shelve
from taskdef import *

# Flask config vars
app = Flask(__name__)

# Using a Shelve for persistence of the STATUS dict
app.config['SHELVE_FILENAME'] = 'director'
flask_shelve.init_app(app)

# Prepare our context and socket to push jobs to workers 
context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.bind("tcp://*:2346")

@app.route('/')
def index():
  return 'AudioLab HTTP API Service'
  
@app.route('/new/<file_id>')
def new_file(file_id):
  STATUS = flask_shelve.get_shelve()
  if file_id in STATUS:
    return f"Already have state for {file_id}", 400
  current = {}
  for task in TASKS:
    current[task] = State.INIT.value
    print(current)
    sender.send_string(f"{task} {file_id}")
  STATUS[file_id] = current
  return f"Sent to Work Queue: {task} {file_id}"

@app.route('/requeue/<file_id>/<task>')
def requeue_task(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  sender.send_string(f"{task} {file_id}")
  return f"Sent to Work Queue: {task} {file_id}"

@app.route('/status/<file_id>')
def file_status(file_id):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  return STATUS[file_id]

@app.route('/update-inprogress/<file_id>/<task>')
def update_inprogress(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  current = STATUS[file_id]
  current[task] = State.PROG.value
  STATUS[file_id] = current
  return "OK"

@app.route('/update-waiting/<file_id>/<task>')
def update_waiting(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  current = STATUS[file_id]
  current[task] = State.WAIT.value
  STATUS[file_id] = current
  return "OK"

@app.route('/update-complete/<file_id>/<task>')
def update_complete(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  current = STATUS[file_id]
  current[task] = State.COMP.value
  STATUS[file_id] = current
  return "OK"

@app.route('/update-failed/<file_id>/<task>')
def update_failed(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  current = STATUS[file_id]
  current[task] = State.FAIL.value
  STATUS[file_id] = current
  return "OK"

@app.route('/update-notavailable/<file_id>/<task>')
def update_notavailable(file_id, task):
  STATUS = flask_shelve.get_shelve()
  if not file_id in STATUS:
    return f"No such file_id {file_id}", 400
  if not task in TASKS:
    return f"No such task {task}", 400
  current = STATUS[file_id]
  current[task] = State.NA.value
  STATUS[file_id] = current
  return "OK"
