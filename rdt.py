from USocket import UnreliableSocket
import threading
import time
import random
from Datagram import *
import utils


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
        self.dst_addr = None
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.debug = debug
        #############################################################################
        # TODO: ADD YOUR NECESSARY ATTRIBUTES HERE
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

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

        while not addr:
            header = None
            while not header:
                data, addr = self.recvfrom(1024)
                header = Datagram(data)
                if not header.check():
                    header = None

            print("Accept: ", addr)
            if header.is_syn():

                conn.dst_addr = addr
                def send_temp(d):
                    conn.sendto(d, conn.dst_addr)
                conn._send_to = send_temp

                def recv_temp(bufsize):
                    recv_data, address = conn.recvfrom(bufsize)
                    if address == conn.dst_addr:
                        return recv_data
                    else:
                        return recv_temp(bufsize)
                conn._recv_from = recv_temp

                seq = random.randint(0, 2 << 32 - 1)
                seqack = header.get_seq() + 1
                data = Datagram(syn=1, ack=1, seq=seq, seqack=seqack).to_bytes()

                conn._send_to(data)
                print("Send ack to: ", addr)
            else:
                addr = None

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
        seq = random.randint(0, 2 << 32 - 1)
        data = Datagram(syn=1, seq=seq).to_bytes()
        self.sendto(data=data, addr=address)

        data, addr = self.recvfrom(1024)
        rcv_data = Datagram(data)

        if rcv_data.is_syn() and rcv_data.is_ack():
            print("Connect to:", addr)
            self.dst_addr = addr

            def send_temp(d):
                self.sendto(d, self.dst_addr)

            self._send_to = send_temp

            def recv_temp(bufsize):
                recv_data, address = self.recvfrom(bufsize)
                if address == self.dst_addr:
                    return recv_data
                else:
                    return recv_temp(bufsize)

            self._recv_from = recv_temp
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
        data = self._recv_from(bufsize)
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
        bytes = bytes
        self._send_to(bytes)
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

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""
