import time
import zmq

# frontend socket to collect messages from API
context = zmq.Context()
frontend = context.socket(zmq.PULL)
frontend.bind("tcp://*:3456")
# backend socket to distribute tasks to workers
backend = context.socket(zmq.ROUTER)
backend.bind("tcp://*:3457")

# poll both sockets for messages
poller = zmq.Poller()
poller.register(frontend, zmq.POLLIN)
poller.register(backend, zmq.POLLIN)

# push and pop work items here
queue = []

# switch messages forever
while True:
	socks = dict(poller.poll())

	if socks.get(frontend) == zmq.POLLIN:
		message = frontend.recv_multipart()
		print("FRONTEND %s" % message)
		queue.append(message[0])

	if len(queue) > 0 and socks.get(backend) == zmq.POLLIN:
		address, empty, ready = backend.recv_multipart()
		print("BACKEND %s %s" % (address, ready))
		backend.send_multipart([address,b'',queue.pop(0)])
