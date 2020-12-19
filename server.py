from rdt import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()
    while True:
        data = conn.recv(1024)
        print("Receive: ", data)
