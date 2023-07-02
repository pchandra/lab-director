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
        PROTO = f.read().strip().encode('ascii')

    with shelve.open(SHELVE_FILENAME) as store:
        if not 'queue' in store:
            store['queue'] = []

        # Switch messages forever
        _log("Starting up router with PID: %d" % pid)
        counter = time.time()
        workers = {}
        last_msg = time.time()

        while True:
            # Extract the queue from the shelf
            queue = store['queue']
            time.sleep(0.01)

            # Do time sensitive checks first
            now = time.time()
            if now - last_msg > 1:
                _log("Router is polling for new messages, queue depth: %d" % len(queue))
                last = now

            socks = dict(poller.poll())

            if socks.get(frontend) == zmq.POLLIN:
                message = frontend.recv_multipart()
                tokens = message[0].split()
                task = tokens[0]
                _log("Frontend got task: %s" % message[0])
                if task == b'convert':
                    queue.insert(0, message[0])
                elif message[0] not in queue:
                    queue.append(message[0])

            if socks.get(backend) == zmq.POLLIN:
                address, empty, ready = backend.recv_multipart()
                job = b"noop noop"
                tokens = ready.split()
                proto = tokens[1]
                instance_id = tokens[2]
                # Check protocol version
                if proto != PROTO:
                    job = b"stop stop"
                    _log(f"Worker version mismatch from {instance_id} - Expected: {PROTO}, got: {proto}")
                else:
                    acceptable = tokens[3:]
                    for j in queue:
                        if j.split()[0].lower() in acceptable:
                            job = j
                            queue.remove(job)
                            break
                    _log(f"Worker {instance_id}-{address.hex()} reports ready, sending: {job}")
                workers[address] = (job, instance_id, time.time())
                backend.send_multipart([address, b'', job])
            # Put the queue back into the shelf for persistence
            store['queue'] = queue
            store.sync()

if __name__ == '__main__':
    main()
