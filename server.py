from rdt import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()
    # print(conn.dst_addr, addr)
    file = open("alice1.txt", mode='w')
    # while True:
    #     data = conn.recv(1024)
    #     print("-----------------------")
    #     print("Server Receive: ", data)
    #     print("-----------------------")
    #     file.write(data.decode())

    data = conn.recv(1024000000)
    print("-----------------------")
    print("Server Receive: ", data)
    print("-----------------------")
    file.write(data.decode())
    file.flush()
