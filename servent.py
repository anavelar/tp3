# SERVENT #

"""
Nome:       Ana Luiza de Avelar Cabral
Matricula:  2013007080
Nome:       Matheus Paiva Costa
Matricula:  2012055170
Nome:       Ramiro Costa Lopes
Matricula:  2013007722
"""

TAM_MAX = 54 #tam max eh 54, mais folga? por isso 60. 52=2+2+(4+2)+4+40, msg entre servents, a maior possivel.

import socket
import sys
import struct

#Historico de mensagens ja lidas/inundadas pelo Servent
class Historico(object):

    def adiciona(self, item):
        if self.size == 10:
            self.lista.pop(0)
            self.size = self.size - 1
        self.lista.append(item)
        self.size = self.size + 1

    def __init__(self):
        self.lista = list()
        self.size = 0
        return self

    def check (self, ip, port, seq, chave):
        item = (ip, port, seq, chave)
        if self.lista.count(item) == 0 :
            self.adiciona(item)
            return true
        else:
            return false

#Banco de Dados de um Servent, que armazena as chaves dele
class BancoDeDados(object):

    def __init__(self, arquivo):
        self.f = open(arquivo, 'r')
        self.dic = {}
        self.populaBD()
        self.f.close()

    def populaBD(self):
        linha = self.f.readline()
        linha = linha[:-1]

        while (linha != ""):    #Enquanto nao chegou ao fim do arquivo
            aux = linha.split(None,1)
            if(not aux[0].startswith('#')):     #linha nao comeca com comentario
                self.dic[aux[0]] = aux[1]
            linha = f.readline()
            linha = linha[:-1]

    def existeChave(self, chaveEntrada):
        return (self.dic.has_key(chaveEntrada))

    def buscaValorAssociado(self, chave): #uma vez existente a chave, busca seu valor
        return (self.dic.get(chave))

#Servent
class Servent(object):

    #Inicializa
    def __init__(self):
        self.sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockServer.bind(("0.0.0.0", int(sys.argv[1])))
        self.bd = BancoDeDados(sys.argv[2]) #Le as chaves e cria BD do servent
        #Cria a lista de vizinhos numa estrutura de vizinhos
        self.historico = Historico()
        self.numSeqReq = 0

    def enviaResponse(self, chave, valor, ipDestino, portoDestino):
        #Empacota
        string = chave + '\t' + valor + '\0'
        packedString = struct.pack('!{}s'.format(len(string)), string)
        packedTipo = struct.pack('!H', 3)
        msgEnvio = packedTipo + packedString

        #Envia
        self.sockServer.sendto(msgEnvio, (ipDestino, portoDestino))

    def trataRequisicao(self, receb):
        self.numSeqReq = self.numSeqReq + 1

        packedChave = receb[0][2:]  #Chave, packed como chegou
        IPcliente = receb[1][0]     #Como String pronto p uso
        portaCliente = receb[1][1]  #Como int pronto p uso
        unpackedChave = struct.unpack('!{}s'.format(len(packedChave)), packedChave)

        #Adiciona essa consulta ao historico de consultas
        self.historico.adiciona((IPcliente, portaCliente, self.numSeqReq, unpackedChave))

        #Monta QUERY para enviar
        packedTipo = struct.pack('!H', 2)
        packedTTL = struct.pack('!H', 3)
        packedIP = socket.inet_aton(IPcliente)
        packedPorta = struct.pack('!H', portaCliente)
        packedNumSeq = struct.pack('!I', self.numSeqReq)

        msgEnvio = packedTipo+packedTTL+packedIP+packedPorta+packedNumSeq+packedChave

        #Envia QUERY para todos os vizinhos
        #ideia so, depende da estrtura de dados:
        #for vizinho in estruturaDadosVizinhos:
        #   self.sockServer.sendto(msgEnvio, (ipDoVizinhoComoString,portaVizinhoComoInt))

        #Busca a chave em seu proprio dicionario
        if (self.bd.existeChave(unpackedChave)): #Se o servent tem essa chave em seu dicionario
            valor = self.bd.buscaValorAssociado(unpackedChave)
            self.enviaResponse(unpackedChave, valor, IPcliente, portaCliente)

    def trataQuery(self, receb):
        unpackedTTL = struct.unpack('!H', receb[0][2:4])
        unpackedIP = socket.inet_ntoa(receb[0][4:8])
        unpackedPorta = struct.unpack('!H', receb[0][8:10])
        unpackedNumSeq = struct.unpack('!I', receb[0][10:14])
        unpackedChave = struct.unpack('!{}s'.format(len(receb[0][14:])), receb[0][14:])

        #Caso seja uma QUERY nova
        if (self.historico.check(unpackedIP, unpackedPorta, unpackedNumSeq, unpackedChave)) #Se a query eh nova, e ja a adiciona no historico

            #Procura por essa chave em seu dicionario local e se achar envia para o cliente
            if (self.bd.existeChave(unpackedChave)): #Se o servent tem essa chave em seu dicionario
                valor = self.bd.buscaValorAssociado(unpackedChave)
                self.enviaResponse(unpackedChave, valor, unpackedIP, unpackedPorta)

            #DAQUI PRA BAIXO FICA DENTRO DO IF DE QUERY NOVA OU NAO??**************************DUVIDA PROTOCOLO OSPF
            #caso nao, chegar todos um pra tras (seleciona e da shift+tab)

            #Decrementa TTL. Se valor resultante for maior do que zero, envia para todos os vizinhos menos o que recebu
            novoTTL = unpackedTTL - 1
            if (novoTTL > 0):
                #Remonta msg com novo TTL
                packedNovoTTL = struct.pack('!H', novoTTL)
                msgEnvio = receb[0][0:2]+ packedNovoTTL + receb[0][4:]
                #Envia QUERY para todos os vizinhos menos o que recebeu:
                #ideia so, depende da estrtura de dados:
                #for vizinho in estruturaDadosVizinhos:
                #   if (AddrVizinho != (receb[1][0], int(receb[1][1]) ) # receb[1][0] eh o String do IP do servent que mandou pra ele,
                                                                        # e receb[1][1] eh o string do porta do servent que mandou pra ele,
                                                                        # que com int(receb[1][1]) converti em inteiro para fazer uma porta int.
                #       self.sockServer.sendto(msgEnvio, (ipDoVizinhoComoString,portaVizinhoComoInt))


    def recebeMensagem(self):
        recebido = self.sockServer.recvfrom(TAM_MAX)
        packed_tipo = recebido[0][0:2]      #primeiros 2 bytes da msg recebida
        tipo = struct.unpack('!H', packed_tipo)
        if(tipo == 1): #Caso essa msg recebida seja um CLIREQ
            self.trataRequisicao(recebido)
        else:
            if(tipo == 2): #Caso essa msg recebida seja uma QUERY
                self.trataQuery(recebido)

    def mainLoop(self):
        while 1:
            self.recebeMensagem()
            #continuar aqui


#Execucao do Programa
servent = Servent()
servent.mainLoop()
