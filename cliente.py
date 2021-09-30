from sys import stdin
from select import select

import socket

# pede para o usuário digitar o endereço do arquivo e palavra
def msg_type():
	print("Digite listar para 'listar' ususários ativos")
	print("Digite id_usuario';'msg para mandasr mensagem para id_usuário")
	print("Digite 'estado' para ver seu estado.")
	print("Digite 'mudar' para mudar seu estado (ativo para inativo ou vice-versa).")
	print("Digite 'historico id' para ver o histórico de uma conversa.")
	print("Digite 'id' para ver seu id no servidor")
	print("\tDigite 'sair' para sair\n")




history = {}

#mostra histórico de conversa com o usuário com esse id
def print_history(id):
	if(id in history):
		for m in history[id]: 
			print(m+'\n')

#decodifica a mensagem de retorno
def decode_ret(msg):
	if(msg[0] == '\x00'):
		id_from, m = msg[1:].split('\x00')
		if(id_from == "-1"):
			print("Mensagem do servidor: "+m)
		else:
			print("Nova mensagem de "+str(id_from)+"!")
			if(id_from not in history):
				history[id_from] = []	
			history[id_from].append(m)
			
	else:
		print("Usuários ativos:")
		activeUsers = msg.split('\x00')
		for u in activeUsers:
			print(u)




def encode_input(msg):
	if msg.find(";") != -1:
		return msg.replace(";", "\x00", 1)
	elif(msg == "listar"):
		return '\x00'
	elif(msg == "estado"):
		return '\x01'
	elif(msg == "mudar"):
		return '\x02'
	elif(msg == "id"):
		return '\x03'
	else:
		raise Exception("wrong input format")
	
	
HOST = 'localhost' # maquina onde esta o servidor
PORTA = 5003 # porta que o servidor esta escutando

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
		


