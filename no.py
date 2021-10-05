from sys import stdin
from select import select
import threading
import socket
import sys
import hashlib


def dotenv(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=', 1))
                    for line in f.readlines() if not line.startswith('#'))

env = dotenv(".env")

HOST = '' # maquina onde esta o servidor

if(len(sys.argv) <= 3):
	print("./no.py porta chave total_de_nos")
	exit()

PORT = int(sys.argv[1])
key = int(sys.argv[2])
N = int(sys.argv[3])

active = False
value = -1
ids = []

sock = socket.socket()
sock.bind((HOST, PORT))
sock.listen(5)
sock.setblocking(False)

def parse(msg):
	global active
	# ping
	if msg == b'\x02':
		# pong
		# ativo
		if(active):
			return b'\x03'
		# inativo
		else:
			return b'\x50'			
	# solicitar
	elif msg[0] == 0x12:
		chave = int.from_bytes(msg[1:], 'big')%N
		print("Recebido chave de busca", str(chave))
		return b'\x14' + str(chave).encode()
	# mudar (estado)
	elif msg == b'\x19':
		active = not active
		return b'\x20' if active else b'\x21'
	else:
		return None


def no_connection(cnnSocket, id, end):
	while True:
		msg = cnnSocket.recv(1024)
		# se o cliente desconectou
		if not msg: break
		d = parse(msg)
		if d != None:
			cnnSocket.send(d)

	cnnSocket.close()

while True:
	rlist, wlist, xlist = select([sock], [], [])
	for newInput in rlist:
		if newInput == sock:
			newSock, end = sock.accept()
			client = threading.Thread(target = no_connection, args=(newSock, len(ids), end))
			ids.append(client)
			client.start()

for c in ids:
	c.join()
