from rdt import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()

    # while True:
    #     data = conn.recv(1024)
    #     print("-----------------------")
    #     print("Server Receive: ", data)
    #     print("-----------------------")
    #
    #     if data == b'exit':
    #         break


    while True:
        data = input(">")
        conn.send(data.encode())

        if data == 'exit':
            break

    # with open("dst/补充说明1.pdf", mode='wb') as file:
    #     data = conn.recv(1024000000)
    #     print("-----------------------")
    #     print("Server Receive!")
    #     print("-----------------------")
    #     file.write(data)

    # with open("2-1-1.PNG", mode='wb') as file:
    #     data = conn.recv(1024000000)
    #     print("-----------------------")
    #     print("Server Receive")
    #     print("-----------------------")
    #     file.write(data)

    # with open("pdf2.pdf", mode='wb') as file:
    #     data = conn.recv(1024000000)
    #     print("-----------------------")
    #     print("Server Receive")
    #     print("-----------------------")
    #     file.write(data)


    conn.close()
