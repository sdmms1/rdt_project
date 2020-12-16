from rdt import socket

SERVER_ADDR,SERVER_PORT = "127.0.0.1", 8080

server = socket()
server.bind(SERVER_ADDR,SERVER_PORT)
while True:
    conn, client = server.accept()
    while True:
        data = conn.recv(2048)
        if not data: break
            conn.send(data)
        conn.close()