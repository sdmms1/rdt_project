from rdt2_0 import RDTSocket
import time

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()

    while True:
        msg = conn.recv(1024)
        print(msg)
        if msg == b'0':
            break

    server.close()
    conn.close()
    print("Program exit!")
