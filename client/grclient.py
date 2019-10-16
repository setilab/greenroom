#!/usr/bin/python

import socket
import sys
import os

_HOST_ = os.getenv("GR_CNTRLR_HOST")
_PORT_ = os.getenv("GR_CNTRLR_PORT")

if len(_HOST_) > 0:
    HOST = _HOST_
else:
    HOST = "localhost"

if len(_PORT_) > 0:
    PORT = _PORT_
else:
    PORT = 12000

data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(data + "\n")

    # Receive data from the server and shut down
    while True:
	received = sock.recv(1024)
	if len(received) > 0:
        	print "{}".format(received)
	else:
		break

finally:
    sock.close()

