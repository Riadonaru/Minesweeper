import socket
import threading
from typing import Dict

from classes import CLIENTS, Communicator, Client

# HOST = '10.100.102.24'
HOST = '127.0.0.1'
PORT = 65432
RECVR: Client = None

ServerSideSocket = socket.socket()
try:
    ServerSideSocket.bind((HOST, PORT))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(5)


def inputListener():

    global RECVR, ServerSideSocket

    comm = Communicator()
    while True:
        inp = input().split(maxsplit=1)
        if inp[0] != "quit":
            if inp[0] == "client":
                RECVR = CLIENTS[int(inp[1])]
            
            if RECVR is not None:
                comm.pipe(RECVR, inp[0] + " " + inp[1])
            else:
                print("Can't execute command as no client was chosen")
        else:
            ServerSideSocket.close()
            break


def mineSweeper(client: Client):

    global NUM_OF_THREADS

    comm = Communicator()
    with client.socket:
        while True:
            data = comm.listen(client)
            print(data)
            if not data:
                break

        del CLIENTS[client.id]
        NUM_OF_THREADS -= 1


def snake():
    pass

CLIENT_TYPES: Dict[str, callable] = {"minesweeper": mineSweeper,
                                     "snake": snake
                                     }

NUM_OF_THREADS = 0
threading.Thread(target=inputListener).start()
with ServerSideSocket:
    while True:
        clientconn, address = ServerSideSocket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        client = Client(NUM_OF_THREADS, str(
            clientconn.recv(2048), 'ascii'), clientconn)
        client.socket.sendall(bytes('Server recognizes you as %s %s' % (client.type, client.id), 'ascii'))
        if NUM_OF_THREADS == 0:
            RECVR = client
        threading.Thread(target=CLIENT_TYPES[client.type], args=(client,)).start()
        print("%s is connected & handled by thread %s" %
              (client.type, client.id))
        CLIENTS.append(client)
        NUM_OF_THREADS += 1


