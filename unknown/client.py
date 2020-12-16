from rdt import socket

SERVER_ADDR, SERVER_PORT = "127.0.0.1", 8080
BUFFER_SIZE = 500
MESSAGE = "Hello!"

client = socket()
client.connect(SERVER_ADDR, SERVER_PORT)
client.send(MESSAGE)
data = client.recv(BUFFER_SIZE)
assert data == MESSAGE
client.close()