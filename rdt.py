from USocket import UnreliableSocket
from threading import *
import time
import random
from Datagram import *
import utils
from multiprocessing import SimpleQueue

class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)

    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode. 
    https://docs.python.org/3/library/socket.html#socket-timeouts

    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.debug = debug
        #############################################################################
        # TODO: ADD YOUR NECESSARY ATTRIBUTES HERE
        #############################################################################
        self.dst_addr = None
        self.send_queue = SimpleQueue()
        self.send_thread = None

        self.recv_queue = SimpleQueue()
        self.recv_thread = None
        self.recv_data_buffer = [b'']
        self.process_thread = None

        self.seq = -1
        self.seqack = -1

        self.start_idx, self.bias= 0, 0
        self.win_size, self.data_len = 20, 1000
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def thread_start(self):
        self.send_thread = Thread(target=self.send_threading)
        self.send_thread.start()
        self.recv_thread = Thread(target=self.recv_threading)
        self.recv_thread.start()
        self.process_thread = Thread(target=self.process_threading)
        self.process_thread.start()

    def send_threading(self):
        while True:
            # print("check send queue")
            if self.send_queue.empty():
                time.sleep(0.00001)
            else:
                data = self.send_queue.get()
                self.sendto(data, self.dst_addr)

    def recv_threading(self):
        while True:
            recv_data, address = self.recvfrom(2048)
            if address == self.dst_addr:
                # print("Receive:")
                self.recv_queue.put(recv_data)

    def process_threading(self):
        while True:
            while self.recv_queue.empty():
                time.sleep(0.00001)

            recv_data = Datagram(self.recv_queue.get())
            print("Receive: ", str(recv_data))
            if not recv_data.check():
                continue

            if recv_data.is_fin():
                if recv_data.is_ack():
                    pass
                else:
                    pass
            elif recv_data.is_syn():
                continue
            elif recv_data.is_ack():
                t = recv_data.get_seqack() - self.seq
                self.update_window(t)
            elif recv_data.is_psh():
                pass
            else:
                self.recv_data_buffer[-1] = self.recv_data_buffer[-1] + recv_data.data
                self._send(Datagram(ack=1, seq=self.seq, seqack=recv_data.get_seq() + recv_data.get_len()))
                if recv_data.is_end():
                    self.recv_data_buffer.append(b'')

    def update_window(self, t):
        self.bias -= t / self.data_len
        self.start_idx += t
        self.seq += t

    def _send(self, d: Datagram):
        self.send_queue.put(d.to_bytes())

    def _recv(self):
        while self.recv_queue.empty():
            time.sleep(0.00001)

        return self.recv_queue.get()

    def accept(self) -> ("RDTSocket", (str, int)):
        """
        Accept a connection. The socket must be bound to an address and listening for 
        connections. The return value is a pair (conn, address) where conn is a new 
        socket object usable to send and receive data on the connection, and address 
        is the address bound to the socket on the other end of the connection.

        This function should be blocking. 
        """
        conn, addr = RDTSocket(self._rate), None
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.setblocking(True)

        # TODO: BIND?
        conn.bind(('127.0.0.1', 9999))

        while not addr:
            header = None
            while not header:
                data, addr = self.recvfrom(1024)
                header = Datagram(data)
                if not header.check():
                    header = None

            if header.is_syn():

                conn.dst_addr = addr
                conn.thread_start()

                conn._send_to = conn._send
                conn._recv_from = conn._recv

                conn.seq = random.randint(0, (2 << 32) - 1)
                conn.seqack = header.get_seq() + 1
                data = Datagram(syn=1, ack=1, seq=conn.seq, seqack=conn.seqack)
                conn._send(data)
            else:
                addr = None

        print("Accept: ", addr)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return conn, addr

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.seq = random.randint(0, (2 << 32) - 1)
        data = Datagram(syn=1, seq=self.seq).to_bytes()
        self.sendto(data=data, addr=address)

        rcv_data, addr = Datagram(), None
        while not rcv_data.is_syn() or not rcv_data.is_ack() or rcv_data.get_seqack() != self.seq + 1:
            data, addr = self.recvfrom(1024)
            rcv_data = Datagram(data)

        self.seq = rcv_data.get_seqack()
        self.seqack = rcv_data.get_seq() + 1
        self.dst_addr = addr
        self.thread_start()

        self._send_to = self._send
        self._recv_from = self._recv
        print("Connect to:", addr)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def recv(self, bufsize: int) -> bytes:
        """
        Receive data from the socket. 
        The return value is a bytes object representing the data received. 
        The maximum amount of data to be received at once is specified by bufsize. 
        
        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        data = None
        assert self._recv_from, "Connection not established yet. Use recvfrom instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        while len(self.recv_data_buffer) < 2:
            time.sleep(0.00001)

        data = self.recv_data_buffer[0]
        if len(self.recv_data_buffer[0]) > bufsize:
            self.recv_data_buffer[0] = data[bufsize:]
            data = data[:bufsize]
        else:
            self.recv_data_buffer.pop(0)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return data

    def send(self, bytes: bytes):
        """
        Send data to the socket. 
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        assert self._send_to, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.start_idx, self.bias, final_seq = 0, 0, self.seq + len(bytes)
        self.win_size, self.data_len = 20, 1024

        u, v = 0, 0
        while self.seq < final_seq:
            while self.bias < self.win_size and v < len(bytes):
                u = int(self.start_idx + self.bias * self.data_len)
                v = int(u + self.data_len)
                seq = int(self.seq + self.bias * self.data_len)

                print(u + self.seq, v + self.seq)
                send_data = Datagram(seq=seq, seqack=self.seqack, end=(v >= len(bytes)), data=bytes[u:v])

                # try:
                #     send_data = Datagram(seq=seq, seqack=self.seqack, end=(v >= len(bytes)), data=bytes[u:v])
                # except Exception:
                #     print
                #     print(u,v, "----------------------")

                # print("Send: ", send_data)
                self._send_to(send_data)
                self.bias += 1
            time.sleep(0.00001)

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        data = Datagram(fin=1).to_bytes()
        self.sendto(data=data, addr=self.dst_addr)

        rcv_data = Datagram()
        while not rcv_data.is_fin() or not rcv_data.is_ack():
            data = self.recv(1024)
            rcv_data = Datagram(data)

        self._send_to = None
        self._recv_from = None
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""
