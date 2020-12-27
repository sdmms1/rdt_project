import sys
sys.path.append('D:\\Program\\Project\\rdt-project')

from rdt2_0 import RDTSocket

server_addr = ("127.0.0.1", 9091)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()

    with open("dst/补充说明3.pdf", mode='wb') as file:
        data = conn.recv(1024000000)
        print("-----------------------")
        print("Server Receive!")
        print("-----------------------")
        file.write(data)

    print("Client1 receive!")
    conn.send(data)

    server.close()
    conn.close()
