from rdt import RDTSocket
from threading import *
import time

client_addr = ("127.0.0.1", 9091)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9090))

    # while True:
    #     data = input(">")
    #     client.send(data.encode())
    #
    #     if data == 'exit':
    #         break


    while True:
        data = client.recv(1024)
        print("-----------------------")
        print("Client Receive: ", data)
        print("-----------------------")

        if data == b'exit':
            break

    # start = time.time()
    # data = open("src/补充说明.pdf", 'rb').read()
    # client.send(data)
    # print(time.time() - start)

    # data = open("2-1.PNG", 'rb').read()
    # client.send(data)

    # data = open("pdf1.pdf", 'rb').read()
    # client.send(data)

    print("Finish!")
