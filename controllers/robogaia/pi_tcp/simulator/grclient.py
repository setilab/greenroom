#!/usr/local/bin/python

import socket
import sys

HOST, PORT = "localhost", 12000
txt = " ".join(sys.argv[1:]) + "\n"

data = bytes(txt, 'utf-8')

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(data)

    # Receive data from the server and shut down
    while True:
	received = sock.recv(1024)
	if len(received) > 0:
        	print("{}".format(received.decode()))
	else:
		break

finally:
    sock.close()

