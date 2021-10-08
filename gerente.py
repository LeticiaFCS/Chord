import socket
import select
import sys
import time
import subprocess
import threading
import signal

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
sock.listen(60) 
#torna o socket não bloqueante
sock.setblocking(False)



inputList = [sys.stdin, sock]
ids = []

N = 8
if(len(sys.argv) > 1):
	N = int(sys.argv[1])
#ao menos um nó na rede
if(N == 0):
	N = 1
#o número de nós é a menor potencia de 2 que é pelo menos N
N = 1 << (N.bit_length() - 1)

chord = []


def query(no_port):
	no_socket = socket.socket()
	no_socket.connect((HOST, no_port))
	return no_socket

def comandos():
	print("Comandos:")
	print("\tlistar - lista as portas dos nós ativos")
	print("\tMudar ID - muda o valor do nó ID ( 0 <= ID < N )")
	print("\tsair - fecha o programa")
def init():
	for i in range(N):
		no_port = PORT_NO_PREF + i
		args = 'exec python3 no.py ' + str(no_port) + ' ' + str(i) + ' ' + str(N)
		proc = subprocess.Popen([args], shell=True)
		chord.append((proc, None, no_port))
		
	print("Chord criado! Aguarde a inicializacao")
	
	time.sleep(SLEEP_SOCKET_DELTA)
	change_state(0)
	print("Chord inicializado!")
	
	comandos()
	

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


def closeAll(sig, frame):
	for proc in chord:
		proc[0].terminate()
	sys.exit()

def parse(msg):
	#cliente solicita um no ativo
	if msg == b'\x01':
		no_port = getActive()
		#envia porta de um no ativo
		if no_port > 0:
			return b'\x61' + str(no_port).encode()
		#nao ha nos ativos
		else:
			return b'\x62'

def new_connection(cnnSocket, id):
	while True:
		msg = cnnSocket.recv(1024)
        # se o cliente desconectou
		if not msg: break
		d = parse(msg)
		if d:
			cnnSocket.send(d)

	cnnSocket.close()

#funções auxiliares para fechar o programa sem digitar sair
signal.signal(signal.SIGINT, closeAll)
signal.signal(signal.SIGTSTP, closeAll)
signal.signal(signal.SIGTERM, closeAll)


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
					sock.close()
					closeAll(None, None)					 
					
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
							comandos()
					except Exception:
						print("comando invalido")
						comandos()
	
					
main()

