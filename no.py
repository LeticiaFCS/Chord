from sys import stdin
from select import select

import socket


	
HOST = 'localhost' # maquina onde esta o servidor
PORTA = 5003 # porta que o servidor esta escutando


class no:
	
	def __init__(self, x, N):
		self.value = -1
		self.key = x % N
		self.port = 5010 + aself.key
		
	

"""
# cria socket
sock = socket.socket() 
# conecta-se com o servidor
sock.connect((HOST, PORTA)) 

inputList = [stdin, sock]

msg_type()


while True:
	#select em espera para sock ou entrada padrão
	rlist, wlist, xlist = select(inputList, [], [])
	for newInput in rlist:
		if newInput == sock:
			#espera a resposta do servidor
			returned_msg = sock.recv(1024)			
			decode_ret( str(returned_msg,  encoding='utf-8') )
		elif newInput == stdin:
			line = stdin.readline()
			cmd = line[:-1]
			if(cmd != "sair"):
				if(cmd.startswith("historico ")):
					_, id = cmd.split(' ')
					print_history(id)
				else:
					try:
						msg = encode_input(cmd)		
						# envia uma mensagem para o servidor
						sock.sendall(bytes(msg, "utf8"))
						
						
						
						
					except Exception as e:
						print(e)
			else:
				sock.close()
				exit()
		#msg_type()	
		
"""
