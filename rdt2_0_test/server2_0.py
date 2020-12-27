import sys
sys.path.append('D:\\Program\\Project\\rdt-project')

from rdt2_0 import RDTSocket

server_addr = ("127.0.0.1", 9090)
server = RDTSocket()

if __name__ == '__main__':
    server.bind(server_addr)
    conn, addr = server.accept()
    # conn1, addr1 = server.accept()

    start = time.time()
    with open("dst/补充说明1.pdf", mode='wb') as file:
        data = conn.recv(1024000000)
        print("-----------------------")
        print("Server Receive!")
        print("-----------------------")
        file.write(data)

    print("Client1 receive!")
    conn.send(data)

    # with open("../dst/补充说明3.pdf", mode='wb') as file:
    #     data = conn1.recv(1024000000)
    #     print("-----------------------")
    #     print("Server Receive!")
    #     print("-----------------------")
    #     file.write(data)
    #
    # print("Client2 receive!")
    # conn1.send(data)

    server.close()
    conn.close()
    # conn1.close()

    # while True:
    #     data = input(">")
    #     if data == '0':
    #         conn.close()
    #         conn1.close()
    #         break

    # while True:
    #     data = conn.recv(1024)
    #     print("-----------------------")
    #     print("Server Receive: ", data)
    #     print("-----------------------")
    #
    #     if data == b'exit':
    #         break


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


