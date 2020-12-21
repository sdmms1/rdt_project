from rdt import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()
    # print(conn.dst_addr, addr)
    # while True:
    #     data = conn.recv(1024)
    #     print("-----------------------")
    #     print("Server Receive: ", data)
    #     print("-----------------------")
    #     file.write(data.decode())

    # with open("alice1.txt", mode='w') as file:
    #     data = conn.recv(1024000000).decode()
    #     print("-----------------------")
    #     print("Server Receive!")
    #     print("-----------------------")
    #     file.write(data)

    with open("2-1-1.PNG", mode='wb') as file:
        data = conn.recv(1024000000)
        print("-----------------------")
        print("Server Receive")
        print("-----------------------")
        file.write(data)
