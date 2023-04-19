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

    with shelve.open(SHELVE_FILENAME) as store:
        if not 'queue' in store:
            store['queue'] = []

        # Switch messages forever
        _log("Starting up router with PID: %d" % pid)
        while True:
            # Extract the queue from the shelf
            queue = store['queue']
            time.sleep(1)
            _log("Router is polling for new messages, queue depth: %d" % len(queue))
            socks = dict(poller.poll())

            if socks.get(frontend) == zmq.POLLIN:
                message = frontend.recv_multipart()
                task, file_id = message[0].split()
                _log("Frontend got task: %s" % message[0])
                queue.append(message[0])

            if len(queue) > 0 and socks.get(backend) == zmq.POLLIN:
                address, empty, ready = backend.recv_multipart()
                acceptable = ready.split()[1:]
                job = b"noop noop"
                for j in queue:
                    if j.split()[0] in acceptable:
                        job = j
                        queue.remove(job)
                        break
                _log("Worker %s reports as ready, sending task: %s" % (address.hex(), job))
                backend.send_multipart([address, b'', job])
            # Put the queue back into the shelf for persistence
            store['queue'] = queue
            store.sync()

if __name__ == '__main__':
    main()
