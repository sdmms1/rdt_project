from rdt2_0 import RDTSocket
from threading import *
import time

client_addr = ("127.0.0.1", 9092)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9090))

    while True:
        msg = input(">")
        client.send(msg.encode())
        if msg == '0':
            break

    client.close()
    print("Program exit!")
