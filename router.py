import sys
import time
import zmq
import shelve
import logging
from taskdef import *
from config import CONFIG as conf

SHELVE_FILENAME = conf['ROUTER_SHELVE']
FRONT_BIND = conf['ROUTER_FRONTEND_BIND']
FRONT_PORT = conf['ROUTER_FRONTEND_PORT']
BACK_BIND = conf['ROUTER_BACKEND_BIND']
BACK_PORT = conf['ROUTER_BACKEND_PORT']
HEARTBEAT_TIME = conf['HEARTBEAT_TIME']
LOG_PREFIX = conf['LOG_PREFIX']
LOG_DATEFMT = conf['LOG_DATEFMT']
LOG_LEVEL = conf['LOG_LEVEL']


def main():
    logging.basicConfig(format=LOG_PREFIX, datefmt=LOG_DATEFMT, level=LOG_LEVEL)
    log = logging.getLogger('router')
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
        log.info("Starting up router")
        counter = time.time()
        workers = {}
        last_msg = time.time()

        while True:
            # Extract the queue from the shelf
            queue = store['queue']
            time.sleep(0.01)

            # Do time sensitive checks first
            now = time.time()
            if now - last_msg > HEARTBEAT_TIME:
                log.info("Queue depth: %d" % len(queue))
                last_msg = now

            socks = dict(poller.poll())

            if socks.get(frontend) == zmq.POLLIN:
                message = frontend.recv_multipart()
                tokens = message[0].split()
                task = tokens[0]
                log.info("Received: %s" % message[0])
                if task == f"{Tasks.EXPT.value}".encode('ascii'):
                    queue.insert(0, message[0])
                elif message[0] not in queue:
                    queue.append(message[0])

            if socks.get(backend) == zmq.POLLIN:
                address, empty, ready = backend.recv_multipart()
                job, logf = f"{Tasks.NOOP.value} nonce".encode('ascii'), log.debug
                tokens = ready.split()
                proto = tokens[1]
                instance_id = tokens[2]
                # Check protocol version
                if proto != PROTO:
                    job, logf = f"{Tasks.STOP.value} nonce".encode('ascii'), log.warning
                    log.warning(f"Bad worker version: {proto} (expected: {PROTO}) from {instance_id}")
                else:
                    acceptable = tokens[3:]
                    for j in queue:
                        if j.split()[0].lower() in acceptable:
                            job, logf = j, log.info
                            queue.remove(job)
                            break
                logf(f"Ready: {instance_id}-{address.hex()} sending: {job}")
                workers[address] = (job, instance_id, time.time())
                backend.send_multipart([address, b'', job])
            # Put the queue back into the shelf for persistence
            store['queue'] = queue
            store.sync()

if __name__ == '__main__':
    main()
