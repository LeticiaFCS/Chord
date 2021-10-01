import socket
import select
import sys
import time
import subprocess
import threading

HOST = ''
HOST_NO = 'localhost'
PORTA = 5003 # porta que a aplicacao esta usando
PORT_NO_PREF = 5010

# cria um socket para comunicacao
sock = socket.socket() 
# vincula a interface e porta para comunicacao
sock.bind((HOST, PORTA))
# define o limite maximo de conexoes pendentes e coloca-se em modo de espera por conexao
sock.listen(5) 
#torna o socket não bloqueante
sock.setblocking(False)

inputList = [sys.stdin, sock]

N = 5
if(len(sys.argv) > 1):
	N = int(sys.argv[1])

chord = []

def init():
	for i in range(N):
		no_port = PORT_NO_PREF + i
		proc = subprocess.Popen(['python no.py ' + str(no_port) + ' ' + str(i) + ' ' + str(N)], shell=True)
		sock = socket.socket()
		time.sleep(2)
		print("CONECTANDO AO NO", i, no_port)
		sock.connect((HOST_NO, no_port))
		print("CONECTADO AO NO", i, no_port)
		chord.append((proc, sock, no_port))

def listActive():
	lst = []
	return lst

def closeAll():
	for proc in chord:
		proc[0].terminate()

def main():
	init()
	closeAll()
	# while True:
	# 	#select em espera para sock ou entrada padrão
	# 	rlist, wlist, xlist = select.select(inputList, [], [])

	# 	for newInput in rlist:
	# 		if newInput == sock:
	# 			# aceita a primeira conexao da fila
	# 			"""newSock, endereco = sock.accept() # retorna um novo socket e o endereco do par conectado
	# 			# aceita nova conexão criando nova thread
	# 			client = threading.Thread(target = new_connection, args=(newSock, len(ids)))
				
	# 			ids.append(client)
	# 			sockets.append(newSock)
	# 			clientsActive[len(ids) - 1] = True
	# 			client.start()
	# 			"""
	# 		elif newInput == sys.stdin:
	# 			#le comando digitado pelo usuário na entrada padrão
	# 			cmd = input()
	# 			if(cmd == 'sair'):
	# 				#espera todas as threads ativas terminarem
	# 				"""for client in ids:
	# 					client.join()
	# 				exited = True
	# 				sender.join()
	# 				# fecha o socket principal
	# 				"""
	# 				print("sair")
	# 				sock.close() 
	# 				sys.exit()
	# 			elif(cmd == "listar"):
	# 				print("listar")
	# 			else:
	# 				try:
	# 					comando, id = cmd.split(' ')
	# 					id = int(id)
	# 					if(id < 0 or id >= N):
	# 						raise Exception("")
						
	# 					if(comando == "ativar"):
	# 						print("ativar "+str(id))
	# 					elif(comando == "desativar"):
	# 						print("desativar "+str(id))
						
	# 					else:
	# 						print("comando invalido")
	# 				except Exception:
	# 					print("comando invalido")
					
main()

