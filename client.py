from rdt import RDTSocket

client_addr = ("127.0.0.1", 9091)
client = RDTSocket()

if __name__ == '__main__':
    client.bind(client_addr)
    client.connect(("127.0.0.1", 9090))

    while True:
        data = input(">")
        client.send(data.encode())
