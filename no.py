from sys import stdin
from select import select
import threading
import socket
import sys

HOST = '' # maquina onde esta o servidor

if(len(sys.argv) <= 3):
	print("./no.py porta chave total_de_nos")
	exit()

PORT = int(sys.argv[1])
key = int(sys.argv[2])
N = int(sys.argv[3])

active = True
value = -1
ids = []

sock = socket.socket()
sock.bind((HOST, PORT))
sock.listen(5)
sock.setblocking(False)

def parse(msg):
	global active
	# ping
	if msg[0] == b'\x02' and active:
		# pong
		return b'\x03'
	elif msg[0] == b'\x19':
		active = not active
		return b'\x20' if active else b'\x21'
	else:
		return None


def no_connection(cnnSocket, id):
	while True:
		msg = cnnSocket.recv(1024) 
        # se o cliente desconectou
		if not msg: break
		d = parse(msg)
		if d != None:
			cnnSocket.send(d)

	cnnSocket.close()

while True:
	newSock, _ = sock.accept()
	client = threading.Thread(target = no_connection, args=(newSock, len(ids)))
	ids.append(client)
	client.start()

for c in ids:
	c.join()
