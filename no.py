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

STABILIZE_DELTA = 1

sock = socket.socket()
sock.bind((HOST, PORT))
sock.listen(20)
sock.setblocking(False)

lock = threading.Lock()

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
		#print(key, " SUCESSOR ", suc)
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
	print(key," joined suc = ", suc-PORTA_NOS)
	#stabilize()
	
	

def notify(other_key):
	global pred
	if(pred == None or inOpen(other_key, pred - PORTA_NOS, key)):
		pred = PORTA_NOS + other_key

def stabilize():
	global suc
	#print(PORT-PORTA_NOS, " chamou stabilize ")
	#print("\tSTABILIZE ", key," pred ", (pred if pred else PORTA_NOS-1)-PORTA_NOS, " suc ", suc-PORTA_NOS)
	
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
	#print(key, " fix sucessor = ", id)
	suc = id + PORTA_NOS
	
	
def periodically():
	while(True):	
		time.sleep(STABILIZE_DELTA)			
		with lock:
			if(active):
				stabilize()
		with lock:
			if(active):
				check_predecessor()
		#fix_sucessor()		

def departure():
	#print("\tdepature")
	if(pred != None):
		pred_no = socket.socket()
		pred_no.connect((HOST, pred))
		pred_no.send( b'\x65'+str(suc).encode())
	#	print("\tdepature pred ",pred)
		pred_no.close()
	if(suc != PORT):
		suc_no = socket.socket()
		suc_no.connect((HOST, suc))
		if(pred == None):
			suc_no.send( b'\x66'+"-1".encode())
		else:
			suc_no.send( b'\x66'+str(pred).encode())
	#	print("\tdepature suc")
		suc_no.close()
	print(key," departed ")
	
def get_id(other):
	if(other == PORT):
		return key
	else:
		 other_node = socket.socket()
		 other_node.connect((HOST, other))
		 other_node.send(b'\x07')
		 msg = other_node.recv(10)
		 other_node.close()
		 other_id = int(parse(msg))
		 return other_id

def get_value(other):
	if(other == PORT):
		return value
	else:
		 other_node = socket.socket()
		 other_node.connect((HOST, other))
		 other_node.send(b'\x09')
		 msg = other_node.recv(10)
		 other_node.close()
		 other_value = parse(msg)
		 return other_value
def set_value(other, x):
	global value
	if(other == PORT):
		with lock:
			value = x
	else:
		 other_node = socket.socket()
		 other_node.connect((HOST, other))
		 other_node.send(b'\x11'+x.encode())
		 other_node.close()
		
def parse(msg):
	global active, pred, suc, value
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
	
	# no solicita sucessor
	elif msg[0] == 0x05:
		id = int(msg[1:].decode())
		sucessor = find_sucessor(id)
		
		return (b'\x06' + str(sucessor).encode())
	#retorna porta do n?? sucessor
	elif msg[0] == 0x06:
		return msg[1:].decode()
	#no solicitou id
	elif msg[0] == 0x07:
		return (b'\x08'+str(key).encode())
	#no enviou id
	elif msg[0] == 0x08:
		return msg[1:].decode()
	#no solicitou valor
	elif msg[0] == 0x09:
		return (b'\x10'+str(value).encode())
	#no enviou valor
	elif msg[0] == 0x10:
		return msg[1:].decode()
	#mudar valor do no
	elif msg[0] == 0x11:
		with lock:
			value = msg[1:].decode()
		print("MUDAMOS O VALOR DE ", key, " PARA ", msg[1:].decode())
	#notify
	elif msg[0] == 0x04:
		id = int(msg[1:].decode())
		with lock:
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
	
	#cliente solicita valor	
	elif msg[0] == 0x12:
		chave = int.from_bytes(msg[1:], 'big')%N
		chave_sucessor = find_sucessor(chave)
		porta = PORTA_NOS + chave_sucessor
		print("chave de busca ",chave," sucessor ", chave_sucessor)
		if(get_id(porta) == chave):
			return b'\x14' + str(get_value(porta)).encode()
		else:
			return b'\x13'
	#cliente muda valor	
	elif msg[0] == 0x15:
		chave, novo_valor = msg[1:].split(b'\x16')
		chave = int.from_bytes(chave, 'big')%N
		novo_valor = novo_valor.decode()
		chave_sucessor = find_sucessor(chave)
		porta = PORTA_NOS + chave_sucessor
		print("chave de busca ",chave," sucessor ", chave_sucessor)
		if(get_id(porta) == chave):
			set_value(porta, novo_valor)
			return b'\x17'
		else:
			return b'\x18'
	# mudar (estado)
	elif msg == b'\x19':
		if(active):
			with lock:
				departure()
				active = False
		else:
			with lock:
				join()	
				active = True
		#return b'\x20' if active else b'\x21'
	#sucessor saiu
	elif msg[0] == 0x65:
		new_suc = int(msg[1:].decode())
		with lock:
			#print("\t", key, "new suc: ", new_suc)
			if(suc != new_suc):
				suc = new_suc
			else:
				suc = PORT
			print("\t\t", key," pred ", (pred if pred else PORTA_NOS-1)-PORTA_NOS, " suc ", suc-PORTA_NOS)
	#predecessor saiu
	elif msg[0] == 0x66:
		new_pred = int(msg[1:].decode())
		with lock:
			#print("\t", key, "new pred: ", new_pred)
			if(new_pred != -1):
				pred = new_pred
			else:
				pred = None
			print("\t\t", key," pred ", (pred if pred else PORTA_NOS-1)-PORTA_NOS, " suc ", suc-PORTA_NOS)
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

def debugFunc():
	while(True):
		if(active):
			time.sleep(1)
			print("\t", key," pred ", (pred if pred else PORTA_NOS-1)-PORTA_NOS, " suc ", suc-PORTA_NOS)

stabilizeTread = threading.Thread(target = periodically, args=())
stabilizeTread.start()

#debugTread = threading.Thread(target = debugFunc, args=())
#debugTread.start()

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





