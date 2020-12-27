from socket import *
from time import ctime
from threading import Thread
from multiprocessing import SimpleQueue

queue = SimpleQueue()

def communicate():
    HOST = ''
    PORT = 21567
    BUFSIZ = 1024
    ADDR = (HOST, PORT)

    tcpSerSock = socket(AF_INET, SOCK_STREAM)
    tcpSerSock.bind(ADDR)
    tcpSerSock.listen(5)
    while True:
        print('waiting for connection...')
        tcpCliSock, addr = tcpSerSock.accept()
        print('...connnecting from:', addr)

        while True:
            data = tcpCliSock.recv(BUFSIZ)
            if not data:
                break
            print("Put into queue")
            tcpCliSock.send(data)
            queue.put(data)
            # tcpCliSock.send('[%s] %s' %(bytes(ctime(),'utf-8'),data))
            tcpCliSock.send(('[%s] %s' % (ctime(), data)).encode())
        tcpCliSock.close()

    tcpSerSock.close()

def out():
    cnt = 1
    while True:
        if cnt % 10000000 == 0:
            if queue.empty():
                print(cnt)
            else:
                data = queue.get()
                print(data)
        cnt += 1


t1 = Thread(target=communicate)
t1.start()
t2 = Thread(target=out)
t2.start()

