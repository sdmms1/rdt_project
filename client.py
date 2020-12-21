from rdt import RDTSocket
from threading import *

client_addr = ("127.0.0.1", 9091)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9090))

    # while True:
    #     data = input(">")
    #     client.send(data.encode())

    # data = open("alice.txt", 'r').read().encode()
    # client.send(data)

    data = open("2-1.PNG", 'rb').read()
    client.send(data)

    print("Finish!")
