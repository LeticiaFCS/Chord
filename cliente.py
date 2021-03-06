from sys import stdin
from select import select

import socket


def dotenv(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=', 1))
                    for line in f.readlines() if not line.startswith('#'))

env = dotenv(".env")

HOST_NO = 'localhost'
HOST_GERENTE = 'localhost' # maquina onde esta o servidor
PORTA_GERENTE = int(env['PORTA_GERENTE']) # porta que o servidor esta escutando

# cria socket
sockGerente = socket.socket()
# conecta-se com o servidor
sockGerente.connect((HOST_GERENTE, PORTA_GERENTE))

inputList = [stdin, sockGerente]

def parse(msg):
	#recebeu porta de um no ativo
	if msg[0] == 0x61:
		return msg[1:]
	#recebeu valor do no
	elif msg[0] == 0x14:
		return msg[1:]
	#mudou valor do no com sucesso
	elif msg[0] == 0x17:
		return True
	return None

def getActive():
	sockGerente.send(b'\x01')
	msg = sockGerente.recv(10)
	d = parse(msg)
	if d:
		return int(d.decode())
	return -1

def solicitar(chave, port):
	sock_no = socket.socket()
	sock_no.connect((HOST_NO, port))
	sock_no.send(b'\x12' + chave.encode())
	msg = sock_no.recv(1024)
	print("Cliente recebeu", msg, "do no", port)
	d = parse(msg)
	if d:
		print("o valor do no de chave ", chave," e ", d.decode())
	else:
		print("O no de chave ", chave," esta inativo")
	sock_no.close()
	
def mudar_valor(chave, valor, port):
	sock_no = socket.socket()
	sock_no.connect((HOST_NO, port))
	sock_no.send(b'\x15' + chave.encode() + b'\x16' + valor.encode())
	msg = sock_no.recv(1024)
	print("Cliente recebeu", msg, "do no", port)
	
	
	d = parse(msg)
	if d:
		print("o valor do no de chave ", chave," foi mudado para ", valor)
	else:
		print("o valor do no de chave ", chave," nao foi mudado")
	sock_no.close()

while True:
	#select em espera para sock ou entrada padrão
	rlist, wlist, xlist = select(inputList, [], [])
	for newInput in rlist:
		if newInput == sockGerente:
			#espera a resposta do servidor
			returned_msg = sockGerente.recv(1024)			

		elif newInput == stdin:
			line = stdin.readline()
			cmd = line[:-1]
			args = cmd.split(" ", 2)
			if len(args) == 1 and args[0] == "sair":
				sockGerente.close()
				exit()
			elif len(args) == 2 and args[0] == "solicitar":
				command, chave = args
				port = getActive()
				if port != -1:
					solicitar(chave, port)
			elif len(args) == 3 and args[0] == "mudar":
				command, chave, valor = args
				port = getActive()
				if port != -1:
					mudar_valor(chave, valor, port)
