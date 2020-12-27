from rdt2_0 import RDTSocket
from threading import *
import time

client_addr = ("127.0.0.1", 9095)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9090))

    start = time.time()
    with open("../src/补充说明.pdf", 'rb') as file:
        data = file.read()
    client.send(data)

    with open("../dst/补充说明2.pdf", mode='wb') as file:
        data = client.recv(1024000000)
        print("-----------------------")
        print("Server Receive!", time.time() - start)
        print("-----------------------")
        file.write(data)

    client.close()
    print("Program exit!")

    # while True:
    #     data = input(">")
    #     client.send(data.encode())
    #
    #     if data == 'exit':
    #         break

    # start = time.time()
    # data = open("src/补充说明.pdf", 'rb').read()
    # client.send(data)
    # print(time.time() - start)

    # data = open("2-1.PNG", 'rb').read()
    # client.send(data)

    # data = open("pdf1.pdf", 'rb').read()
    # client.send(data)

    # print("Finish!")
