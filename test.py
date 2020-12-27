from USocket import *
from threading import Thread, Timer
from socket import *

server_addr = ('127.0.0.1', 8088)
client_addr = ('127.0.0.1', 8089)


class Test:
    def __init__(self):
        self.cnt = 0

    def out(self, i):
        print(self.cnt, i)

    def set(self, i):
        t = Timer(2, self.out, [i])
        t.start()
        time.sleep(3)
        t.start()


def out(i):
    print(i)


def improve(i):
    result = i
    for _ in range(i + 1):
        result += 1 / i
    print(i, result)


if __name__ == '__main__':
    # for i in range(10):
    dir = []
    if len(dir) > 0 and dir[0] == 1:
        print("hahahha")
