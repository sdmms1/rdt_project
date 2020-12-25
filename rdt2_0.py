from USocket import UnreliableSocket
from threading import *
import time
import random
from Datagram import *
import utils
from multiprocessing import SimpleQueue
from enum import Enum


class Status(Enum):
    Closed = 0
    Active = 1
    Active_fin1 = 2
    Active_fin2 = 3
    Passive_fin1 = 4
    Passive_fin2 = 5


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

        self.send_queue = SimpleQueue()  # 等待被发送出去的bytes
        self.recv_queue = SimpleQueue()  # 接受的未被转换的bytes
        self.transmit_queue = SimpleQueue()  # 需要发送的数据
        self.waiting_for_ack = {}
        self.recv_datagram_buf = {}  # 乱序到达的datagram
        self.recv_data_buffer = [b'']  # 收到的数据缓存
        self.recv_data_lock = Lock()

        # 收发记录
        self.ack_cnt = 0
        self.data_cnt = 0
        self.seq = -1
        self.seqack = -1
        self.seq_bias = 0

        # 记录窗口状态
        self.win_idx, self.win_threshold = 0, 20

        # 记录系统状态
        self.isSending = 0
        self.status = Status.Closed

        # 用于设置超时时间
        self.SRTT = 0
        self.DevRTT = 0
        self.RTO = 3
        self.RTT_buf = []

        # 客户地址与对应端口
        self.conns = {}
        self.conn = None

        # 线程相关
        self.status = Status.Active
        self.send_thread = Thread(target=self.send_threading)
        self.recv_thread = Thread(target=self.recv_threading)
        self.transmit_thread = Thread(target=self.transmit_threading)
        self.process_thread = Thread(target=self.process_threading)
        self.fin_thread = None
        self.timers = {}
        self.transmit_thread.start()
        self.process_thread.start()
        self.recv_thread.start()
        self.send_thread.start()
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
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.conn = None

        while not self.conn:
            time.sleep(0.1)

        print("Client address: ", self.conn.dst_addr)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return self.conn, self.conn.dst_addr

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.seq = random.randint(0, (2 << 32) - 1)
        datagram = Datagram(syn=1, seq=self.seq)
        while not self.dst_addr:
            self.sendto(datagram.to_bytes(), address)
            time.sleep(0.5)

        print("Connect to: ", self.dst_addr, " successfully!")
        self.status = Status.Active
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
        assert self.status == Status.Active, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        while len(self.recv_data_buffer) < 2 and len(self.recv_data_buffer[0]) < bufsize:
            time.sleep(0.01)

        with self.recv_data_lock:
            data = self.recv_data_buffer[0]
            if len(data) >= bufsize:
                print("Get part of data at [0]!")
                self.recv_data_buffer[0] = data[bufsize:]
                data = data[:bufsize]
            else:
                print("Get data at [0]!")
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
        assert self.status == Status.Active, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################

        u = 0
        v = DATA_LEN
        while u < len(bytes):
            self.transmit_queue.put({'data': bytes[u:v], 'is_end': v >= len(bytes)})
            u = v
            v += DATA_LEN

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        assert self.status in (Status.Active, Status.Passive_fin1), (self.dst_addr, self.status)
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################

        if not self.dst_addr:
            self._close()
        else:
            if self.status == Status.Active:
                self.status = Status.Active_fin1
            elif self.status == Status.Passive_fin1:
                self.status = Status.Passive_fin2

            while not self.transmit_queue.empty():
                time.sleep(1)

            self._send(datagram=Datagram(fin=1))
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def send_threading(self):
        # socket 状态为closed并且无等待发送的消息时关闭
        while True:
            if self.send_queue.empty():
                if self.status == Status.Closed:
                    break
                time.sleep(0.0001)
            else:
                data = self.send_queue.get()
                self.sendto(data, self.dst_addr)
                print("Send: ", str(Datagram(data)))

            time.sleep(0.00001)

    def recv_threading(self):
        # socket 状态为closed时关闭
        self.settimeout(2)
        while True:
            try:
                recv_data, address = self.recvfrom(8192)
            except Exception:
                if self.status == Status.Closed:
                    break
                continue
            self.recv_queue.put({'data': recv_data, 'address': address})

    def transmit_threading(self):
        while True:
            while len(self.waiting_for_ack) < self.win_threshold and not self.transmit_queue.empty():
                transmit_data = self.transmit_queue.get()
                seq = self.seq + self.seq_bias
                datagram = Datagram(seq=seq, seqack=self.seqack,
                                    end=transmit_data['is_end'], data=transmit_data['data'])
                self.seq_bias += datagram.get_len()
                self.waiting_for_ack[datagram.get_seq()] = datagram
                self._send(datagram)

            if self.transmit_queue.empty() and self.status == Status.Closed:
                break

            time.sleep(0.01)

    def process_threading(self):
        # socket 状态为closed且没有未处理消息时关闭
        while True:
            while self.status != Status.Closed and self.recv_queue.empty():
                time.sleep(0.0001)

            if self.status == Status.Closed:
                break

            msg = self.recv_queue.get()
            recv_data, address = Datagram(msg['data']), msg['address']
            print("Receive: ", str(recv_data))

            if not recv_data.check() and address == self.dst_addr:
                continue

            if recv_data.is_syn():
                if recv_data.is_ack():
                    self.syn_ack_callback(recv_data, address)
                else:
                    self.syn_callback(recv_data, address)
            elif address == self.dst_addr:
                if recv_data.is_fin():
                    if recv_data.is_ack():
                        self.fin_ack_callback()
                    else:
                        self.fin_callback()
                else:
                    self.recv_data_callback(recv_data)

    def _send(self, datagram: Datagram):
        self.send_queue.put(datagram.to_bytes())

    def _close(self):
        print("Closed socket to ", self.dst_addr)
        while not self.send_queue.empty() or not self.recv_queue.empty() or not self.transmit_queue.empty():
            time.sleep(1)
        self.status = Status.Closed
        while self.send_thread.is_alive() or self.recv_thread.is_alive():
            time.sleep(2)
        print("Socket to ", self.dst_addr, "closed!")
        super().close()

    def syn_callback(self, recv_datagram, dst_addr):
        if dst_addr in self.conns:
            print("Already exist conn!")
            self.conn = self.conns[dst_addr]
            self.conn._send(Datagram(syn=1, ack=1))
            return
        elif not self.conn:
            self.conn = RDTSocket(self._rate)
            self.conn.seqack = recv_datagram.get_seq() + 1
            self.conn.seq = random.randint(0, (2 << 32) - 1)
            datagram = Datagram(syn=1, ack=1, seq=self.conn.seq - 1, seqack=self.conn.seqack)
            while True:
                try:
                    address = ('127.0.0.1', random.randint(8080, 65535))
                    self.conn.bind(address)
                    self.conn.sendto(datagram.to_bytes(), dst_addr)
                    print("New socket bind to: ", address)
                    break
                except Exception:
                    print("Fail to bind to ", dst_addr)
            self.conn.dst_addr = dst_addr
            self.conns[dst_addr] = self.conn

    def syn_ack_callback(self, recv_datagram, dst_addr):
        if not self.dst_addr:
            self.seq = recv_datagram.get_seqack()
            self.seqack = recv_datagram.get_seq() + 1
            self.dst_addr = dst_addr

    def fin_callback(self):
        self._send(Datagram(fin=1, ack=1))
        if self.status in (Status.Active_fin1, Status.Active_fin2):
            self._close()
        elif self.status == Status.Active:
            self.status = Status.Passive_fin1

    def fin_ack_callback(self):
        if self.status == Status.Active_fin1:
            self.status = Status.Active_fin2
        elif self.status == Status.Passive_fin2:
            self._close()

    def recv_data_callback(self, recv_datagram: Datagram):
        if recv_datagram.get_len() > 0:
            # 更新 seqack
            self.extract_data(recv_datagram)

        # 更新 seq
        self.update_seq(recv_datagram.get_seqack())

        if self.transmit_queue.empty() and recv_datagram.get_len() != 0:
            self._send(Datagram(seq=self.seq, seqack=self.seqack))

    def extract_data(self, recv_datagram):
        # 提取对方发来的数据并更新seqack
        seq = recv_datagram.get_seq()
        if seq == self.seqack:
            # 取出所有缓存数据包
            self.recv_datagram_buf[seq] = recv_datagram
            while self.seqack in self.recv_datagram_buf:
                datagram = self.recv_datagram_buf.pop(self.seqack)
                self.recv_data_buffer[-1] = self.recv_data_buffer[-1] + datagram.data
                self.seqack = datagram.get_seq() + datagram.get_len()
                if datagram.is_end():
                    self.recv_data_buffer.append(b'')
        elif seq > self.seqack:
            # 缓存乱序数据包
            self.recv_datagram_buf[seq] = recv_datagram

    def update_seq(self, ack):
        if ack > self.seq:
            delete_keys = list(filter(lambda x: x < ack, self.waiting_for_ack.keys()))
            for key in delete_keys:
                datagram = self.waiting_for_ack.pop(key)
                self.seq += datagram.get_len()
                self.seq_bias -= datagram.get_len()
        else:
            # self.seq <= seqack
            pass

    def resend(self):
        pass


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""
