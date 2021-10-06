import socket
import select
import sys
import time
import subprocess
import threading

def dotenv(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=', 1))
                    for line in f.readlines() if not line.startswith('#'))

env = dotenv(".env")

HOST = ''
HOST_NO = 'localhost'
PORTA = int(env['PORTA_GERENTE']) # porta que a aplicacao esta usando
PORT_NO_PREF = int(env['PORTA_NOS']) 
SLEEP_SOCKET_DELTA = 0.2

# cria um socket para comunicacao
sock = socket.socket() 
# vincula a interface e porta para comunicacao
sock.bind((HOST, PORTA))
# define o limite maximo de conexoes pendentes e coloca-se em modo de espera por conexao
sock.listen(20) 
#torna o socket não bloqueante
sock.setblocking(False)



inputList = [sys.stdin, sock]
ids = []

N = 5
if(len(sys.argv) > 1):
	N = int(sys.argv[1])

chord = []


def query(no_port):
	no_socket = socket.socket()
	no_socket.connect((HOST, no_port))
	return no_socket

def init():
	for i in range(N):
		no_port = PORT_NO_PREF + i
		args = 'python3 no.py ' + str(no_port) + ' ' + str(i) + ' ' + str(N)
		proc = subprocess.Popen([args], shell=True)
		chord.append((proc, None, no_port))
	print("Chord criado!")
	
	time.sleep(SLEEP_SOCKET_DELTA)
	change_state(0)
	print("Chord inicializado!")

def getActive():
	for proc in chord:
		sock_cnn = query(proc[2])
		sock_cnn.send(b'\x02')
		resp = sock_cnn.recv(4)
		sock_cnn.close()
		if resp and resp == b'\x03':
			return proc[2]
			
		
	return -1

def listActive():
	lst = []
	for proc in chord:
		sock_cnn = query(proc[2])
		sock_cnn.send(b'\x02')
		resp = sock_cnn.recv(4)
		sock_cnn.close()
		if resp and resp == b'\x03':
			lst.append(proc[2])
		
	print(lst) #DEBUG
	return lst

def change_state(id):
	proc = chord[id]
	sock_cnn = query(proc[2])
	sock_cnn.send(b'\x19')
	sock_cnn.close()


def closeAll():
	for proc in chord:
		proc[0].terminate()

def parse(msg):
	if msg == b'\x01':
		no_port = getActive()
		if no_port > 0:
			return b'\x61' + str(no_port).encode()
		else:
			return b'\x62'

def new_connection(cnnSocket, id):
	print("new connection")
	while True:
		msg = cnnSocket.recv(1024)
        # se o cliente desconectou
		if not msg: break
		d = parse(msg)
		if d:
			cnnSocket.send(d)

	cnnSocket.close()

def main():
	initThread = threading.Thread(target = init, args=())
	initThread.start()
	
	while True:
		#select em espera para sock ou entrada padrão
		rlist, _, _ = select.select(inputList, [], [])

		for newInput in rlist:
			if newInput == sock:
				# aceita a primeira conexao da fila
				newSock, _ = sock.accept() # retorna um novo socket e o endereco do par conectado
				print("AQUI")
				# aceita nova conexão criando nova thread
				client = threading.Thread(target = new_connection, args=(newSock, len(ids)))
				ids.append(client)
				client.start()
			elif newInput == sys.stdin:
				#le comando digitado pelo usuário na entrada padrão
				cmd = input()
				if(cmd == 'sair'):
					#espera todas as threads ativas terminarem
					for client in ids:
						client.join()
					initThread.join()
					# fecha o socket principal
					closeAll()
					sock.close() 
					sys.exit()
				elif(cmd == "listar"):
					listActive()
				else:
					try:
						comando, id = cmd.split(' ')
						id = int(id)
						if(id < 0 or id >= N):
							raise Exception("")
						
						if(comando == "mudar"):
							change_state(id)
						
						else:
							print("comando invalido")
					except Exception:
						print("comando invalido")
	
					
main()

