import sys
import os
from datetime import datetime
import time
import zmq
import shelve
from config import CONFIG as conf

SHELVE_FILENAME = conf['ROUTER_SHELVE']
FRONT_BIND = conf['ROUTER_FRONTEND_BIND']
FRONT_PORT = conf['ROUTER_FRONTEND_PORT']
BACK_BIND = conf['ROUTER_BACKEND_BIND']
BACK_PORT = conf['ROUTER_BACKEND_PORT']

# Logging helper
pid = os.getpid()
def _log(str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stdout.write(f"[{timestamp}] [Router-{pid}] {str}\n")
    sys.stdout.flush()

def main():
    # Frontend socket to collect messages from API
    context = zmq.Context()
    frontend = context.socket(zmq.PULL)
    frontend.bind(f"tcp://{FRONT_BIND}:{FRONT_PORT}")
    # Backend socket to distribute tasks to workers
    backend = context.socket(zmq.ROUTER)
    backend.bind(f"tcp://{BACK_BIND}:{BACK_PORT}")

    # Poll both sockets for messages
    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)

    # Read protocol version string
    with open('version-token') as f:
        proto_ver = f.read().strip().encode('ascii')

    with shelve.open(SHELVE_FILENAME) as store:
        if not 'queue' in store:
            store['queue'] = []

        # Switch messages forever
        _log("Starting up router with PID: %d" % pid)
        counter = 0
        reset = 0
        inprogress = {}
        while True:
            counter += 1
            # Extract the queue from the shelf
            queue = store['queue']
            time.sleep(0.01)
            if counter > 60:
                _log("Router is polling for new messages, queue depth: %d" % len(queue))
                counter = 0
                reset = 0 if len(queue) > 0 else reset + 1
                if reset > 300:
                    reset = 0
                    inprogress = {}
            socks = dict(poller.poll())

            if socks.get(frontend) == zmq.POLLIN:
                message = frontend.recv_multipart()
                task, file_id = message[0].split()
                _log("Frontend got task: %s" % message[0])
                if task.lower() == 'stop':
                    queue.insert(0, message[0])
                elif message[0] not in queue and message[0] not in inprogress.values():
                    queue.append(message[0])

            if len(queue) > 0 and socks.get(backend) == zmq.POLLIN:
                address, empty, ready = backend.recv_multipart()
                job = b"noop noop"
                tokens = ready.split()
                # Check protocol version
                if tokens[1] != proto_ver:
                    job = b"stop stop"
                    _log(f"Worker version mismatch! Expected: {proto_ver}, got: {tokens[1]}")
                else:
                    acceptable = tokens[2:]
                    acceptable.append('stop')
                    for j in queue:
                        if j.split()[0].lower() in acceptable:
                            job = j
                            queue.remove(job)
                            inprogress[address] = job
                            break
                    _log("Worker %s reports as ready, sending task: %s" % (address.hex(), job))
                backend.send_multipart([address, b'', job])
            # Put the queue back into the shelf for persistence
            store['queue'] = queue
            store.sync()

if __name__ == '__main__':
    main()
