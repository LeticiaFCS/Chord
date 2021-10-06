from sys import stdin
from select import select
import threading
import socket
import sys
import hashlib
import time


def dotenv(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=', 1))
                    for line in f.readlines() if not line.startswith('#'))

env = dotenv(".env")

HOST = '' # maquina onde esta o servidor
HOST_GERENTE = 'localhost'
PORTA_GERENTE = int(env['PORTA_GERENTE'])
PORTA_NOS = int(env['PORTA_NOS'])

if(len(sys.argv) <= 3):
	print("./no.py porta chave total_de_nos")
	exit()

PORT = int(sys.argv[1])
key = int(sys.argv[2])
N = int(sys.argv[3])

active = False
value = -1
ids = []
pred = None
suc = PORT

STABILIZE_DELTA = 5

sock = socket.socket()
sock.bind((HOST, PORT))
sock.listen(20)
sock.setblocking(False)


def getActive():
	sockGerente = socket.socket()
	sockGerente.connect((HOST_GERENTE, PORTA_GERENTE))
	sockGerente.send(b'\x01')
	msg = sockGerente.recv(10)
	
	sockGerente.close()
	d = parse(msg)
	if d:
		return int(d.decode())
	return -1


def create():
	global pred, suc
	pred = None
	suc = PORT

def closest_preceding_node(id):
	return suc
	
#(a, b]
def inClose(x, a, b):
	if(x == None or x == -1):
		return False 
	if(a < b):
		return a < x and x <= b
	elif(a > b):
		return a < x or x <= b
	else:
		return True
#(a, b)
def inOpen(x, a, b): 
	if(x == None or x == -1):
		return False 
	if(a < b):
		return a < x and x < b
	elif(a > b):
		return a < x or x < b
	else: 
		return x != a




def find_sucessor(other_key):
	suc_key = suc - PORTA_NOS
	#id in (n, ]
	if(inClose(other_key, key, suc_key)):
		return suc_key
	else:	
		suc_node = socket.socket()
		print(key, " SUCESSOR ", suc)
		suc_node.connect((HOST, suc))
		suc_node.send(b'\x05'+str(other_key).encode())
		msg = suc_node.recv(10)
		suc_node.close()
		return int(parse(msg))
	
def join():
	global suc, key, PORTA_NOS
	node_in_chord = getActive()
	if(node_in_chord == -1):
		create()
	else:
		other = socket.socket()
		other.connect((HOST, node_in_chord))
		other.send(b'\x05'+str(key).encode())
		msg = other.recv(10)
		other.close()
		suc = PORTA_NOS + int(parse(msg))
	print(PORT," joined suc = ", suc)
	#stabilize()
	
	

def notify(other_key):
	print(PORT, " recebeu notify de ", other_key)
	global pred
	if(pred == None or inOpen(other_key, pred - PORTA_NOS, key)):
		pred = PORTA_NOS + other_key

def stabilize():
	print(PORT-PORTA_NOS, " chamou stabilize ")
	global suc
	if(suc == PORT):
		if(pred == None):
			x = -1
		else:
			x = pred - PORTA_NOS
	else:
		suc_node = socket.socket()
		suc_node.connect((HOST, suc))
		suc_node.send(b'\x63')
		msg = suc_node.recv(10)
		suc_node.close()
		x = int(parse(msg))
			
	if(inOpen(x, key, suc - PORTA_NOS)):
		suc = PORTA_NOS + x
	
	if(suc == PORT):
		notify(key)
	else:
		suc_node = socket.socket()
		suc_node.connect((HOST, suc))
		suc_node.send(b'\x04'+str(key).encode())
		suc_node.close()
	
	print(PORT-PORTA_NOS," pred ", (pred if pred else PORTA_NOS-1)-PORTA_NOS, " suc ", suc-PORTA_NOS)
		
def check_predecessor():
	global pred
	if(pred == PORT):
		if(not active):
			pred = None
	elif(pred != None):
		no_pred = socket.socket()		
		no_pred.connect((HOST, pred))
		no_pred.send(b'\x02')
		msg = no_pred.recv(10)
		act = parse(msg)
		if(act and act == b'\x03'):
			return
		pred = None

def fix_sucessor():
	global suc
	id = find_sucessor(key)
	print(key, " fix sucessor = ", id)
	suc = id + PORTA_NOS
	
	
def periodically():
	while(True):		
		if(active):
			print("="*20)
			time.sleep(STABILIZE_DELTA)
			print("="*20)
			stabilize()
			check_predecessor()
			#fix_sucessor()		

def departure():
	print("\tdepature")
	if(pred != None):
		pred_no = socket.socket()
		pred_no.connect((HOST, pred))
		pred_no.send( b'\0x65'+str(suc).encode())
		print("\tdepature pred ",pred)
		pred_no.close()
	if(suc != PORT):
		suc_no = socket.socket()
		suc_no.connect((HOST, suc))
		if(pred == None):
			suc_no.send( b'\0x66'+"-1".encode())
		else:
			suc_no.send( b'\0x66'+str(pred).encode())
		print("\tdepature suc")
		suc_no.close()
	
		
def parse(msg):
	global active, pred, suc
	# ping
	if msg == b'\x02':
		# pong
		# ativo
		if(active):
			return b'\x03'
		# inativo
		else:
			return b'\x50'
	# pong active
	elif msg == b'\x03':
		return msg
	# pong active
	elif msg == b'\x50':
		return msg		
	elif msg[0] == 0x61:
		return msg[1:]	
	# solicitar
	elif msg[0] == 0x05:
		id = int(msg[1:].decode())
		sucessor = find_sucessor(id)
		return (b'\x06' + str(sucessor).encode())
	#retorna porta do nó sucessor
	elif msg[0] == 0x06:
		return msg[1:].decode()
	
	#notify
	elif msg[0] == 0x04:
		id = int(msg[1:].decode())
		notify(id)
		return None				
	#pedido de predecessor
	elif msg[0] == 0x63:
		if(pred == None):
			return (b'\x64' + "-1".encode())
		else:
			return (b'\x64' + str(pred - PORTA_NOS).encode())				
	#recebeu predecessor
	elif msg[0] == 0x64:
		return msg[1:].decode()
		
	elif msg[0] == 0x12:
		chave = int.from_bytes(msg[1:], 'big')%N
		print("Recebido chave de busca", str(chave))
		return b'\x14' + str(chave).encode()
	# mudar (estado)
	elif msg == b'\x19':
		if(active):
			departure()
		else:
			join()	
		active = not active
		#return b'\x20' if active else b'\x21'
	#sucessor saiu
	elif msg[0] == 0x65:
		new_suc = int(msg[1:].decode())
		print("\t", key, "new suc: ", new_suc)
		if(suc != new_suc):
			suc = new_suc
		else:
			suc = PORT
	#predecessor saiu
	elif msg[0] == 0x66:
		new_pred = int(msg[1:].decode())
		print("\t", key, "new pred: ", new_pred)
		if(new_pred != -1):
			pred = new_pred
		else:
			pred = None
	
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



stabilizeTread = threading.Thread(target = periodically, args=())
stabilizeTread.start()

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





