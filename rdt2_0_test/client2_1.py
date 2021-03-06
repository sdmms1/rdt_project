from rdt2_0 import RDTSocket
from threading import *
import time

client_addr = ("127.0.0.1", 9093)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9091))

    start = time.time()
    with open("../src/补充说明.pdf", 'rb') as file:
        data = file.read()
    client.send(data)

    with open("../dst/补充说明4.pdf", mode='wb') as file:
        data = client.recv(1024000000)
        print("-----------------------")
        print("Server Receive!", time.time() - start)
        print("-----------------------")
        file.write(data)

    client.close()
