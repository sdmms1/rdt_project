from rdt2_0 import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()

    with open("../src/补充说明.pdf", 'rb') as file:
        data = file.read()
    conn.send(data)

    with open("../dst/补充说明5.pdf", mode='wb') as file:
        data = conn.recv(1024000000)
        print("-----------------------")
        print("Server Receive!")
        print("-----------------------")
        file.write(data)

    server.close()
    conn.close()
