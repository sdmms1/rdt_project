from USocket import UnreliableSocket
from threading import *
import random
from Datagram import *
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
        # 另一通信方地址，如果是server则为None
        self.dst_addr = None

        self.send_queue = SimpleQueue()  # 等待被发送出去的bytes
        self.recv_queue = SimpleQueue()  # 接受的未被转换的bytes
        self.transmit_queue = SimpleQueue()  # 需要发送的数据 {‘data’:bytes, 'is_end':bool}
        self.waiting_for_send = []  # 已发送等待确认的datagram缓存
        self.timers = {}  # 已发送等待确认的datagram计时器
        self.recv_datagram_buf = {}  # 乱序到达的datagram
        self.recv_data_buffer = [b'']  # 收到的数据缓存
        self.recv_data_lock = Lock()
        self.send_waiting_lock = Lock()
        self.status_lock = Lock()

        # 连接状态
        self.seq = -1
        self.seqack = -1
        self.seq_bias = 0
        self.duplicate_cnt = 0

        # 窗口状态
        self.win_idx, self.win_size = 0, 5

        # 超时设置
        self.SRTT = 3
        self.DevRTT = 0
        self.RTO = 3

        # 已创建的地址与accept()返回的端口
        self.conns = {}
        self.conn = None

        # 线程相关
        self.status = Status.Active
        self.send_thread = Thread(target=self.send_threading)
        self.recv_thread = Thread(target=self.recv_threading)
        self.transmit_thread = Thread(target=self.transmit_threading)
        self.process_thread = Thread(target=self.process_threading)
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
        self.seq = random.randint(2 << 5, 2 << 10)
        datagram = Datagram(syn=1, seq=self.seq)

        # 尝试连接，10次失败后退出
        connect_cnt = 1
        while not self.dst_addr:
            self.sendto(datagram.to_bytes(), address)
            print("Try to connect to ", address)
            connect_cnt += 1
            if connect_cnt > 10:
                print("Fail to connect to server!")
                return
            time.sleep(0.5 * connect_cnt)

        print("Connect to: ", self.dst_addr, " successfully!")
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

        # 获取已收到的数据
        with self.recv_data_lock:
            data = self.recv_data_buffer[0]
            if len(data) >= bufsize:
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
            with self.status_lock:
                if self.status == Status.Active:
                    self.status = Status.Active_fin1
                elif self.status == Status.Passive_fin1:
                    self.status = Status.Passive_fin2

            while not self.transmit_queue.empty():
                time.sleep(1)

            datagram = Datagram(fin=1)
            self._send(datagram=datagram)
            self.set_timer(datagram)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

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
            while len(self.waiting_for_send) < self.win_size and not self.transmit_queue.empty():
                transmit_data = self.transmit_queue.get()
                seq = self.seq + self.seq_bias
                datagram = Datagram(seq=seq, seqack=self.seqack,
                                    end=transmit_data['is_end'], data=transmit_data['data'])
                self.seq_bias += datagram.get_len()
                self.waiting_for_send.append(datagram)

            with self.send_waiting_lock:
                while len(self.waiting_for_send) > self.win_idx and self.win_idx < self.win_size:
                    datagram = self.waiting_for_send[self.win_idx]
                    datagram.update()
                    self._send(datagram)
                    self.set_timer(datagram)
                    self.win_idx += 1

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

    def syn_callback(self, recv_datagram, dst_addr):
        if dst_addr in self.conns and self.conns[dst_addr].status == Status.Active:
            print("Already exist conn!")
            self.conn = self.conns[dst_addr]
            self.conn._send(Datagram(syn=1, ack=1, seq=self.conn.seq - 1, seqack=self.conn.seqack))
            return
        elif not self.conn:
            self.conn = RDTSocket(self._rate)
            self.conn.seqack = recv_datagram.get_seq() + 1
            self.conn.seq = random.randint(2 << 5, 2 << 10)
            self.conn.SRTT = max(1, time.time() - bytes2time(recv_datagram.get_time()))
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
            self.SRTT = max(1, time.time() - bytes2time(recv_datagram.get_time()))

    def fin_callback(self):
        with self.status_lock:
            self.recv_data_buffer.append(b'')
            self._send(Datagram(fin=1, ack=1))
            if self.status in (Status.Active_fin1, Status.Active_fin2):
                self._close()
            elif self.status == Status.Active:
                self.status = Status.Passive_fin1

    def fin_ack_callback(self):
        with self.status_lock:
            if self.status == Status.Active_fin1:
                self.status = Status.Active_fin2
            elif self.status == Status.Passive_fin2:
                self.status = Status.Closed
                self._close()

    def recv_data_callback(self, recv_datagram: Datagram):

        self.update_RTT(recv_datagram)
        if recv_datagram.get_len() > 0:
            # 有需要接收的数据，更新seqack
            self.extract_data(recv_datagram)

        # 更新 seq
        if not self.update_seq(recv_datagram.get_seqack()) and len(self.waiting_for_send) > 0:
            # duplicate ack
            self.resend(datagram=self.waiting_for_send[0], timeout=False)

        if self.transmit_queue.empty() and recv_datagram.get_len() != 0:
            # 没有待发送数据且对方传的数据需要确认，直接发空数据包
            self._send(Datagram(seq=self.seq, seqack=self.seqack))

    def update_RTT(self, datagram: Datagram):
        RTT = (time.time() - bytes2time(datagram.get_time())) * 2
        self.SRTT = self.SRTT + 0.125 * (RTT - self.SRTT)
        self.DevRTT = 0.75 * self.DevRTT + 0.25 * abs(RTT - self.SRTT)
        self.RTO = 1 * self.SRTT + 4 * self.DevRTT
        print("RTT: %f SRTT: %f RTO: %f WIN: %f" % (RTT, self.SRTT, self.RTO, self.win_size))

    def extract_data(self, recv_datagram):
        # 提取对方发来的数据并更新seqack
        seq = recv_datagram.get_seq()
        if seq == self.seqack:
            # 取出所有缓存数据包
            with self.recv_data_lock:
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
            self.duplicate_cnt = 0
            with self.send_waiting_lock:
                while len(self.waiting_for_send) > 0 and self.waiting_for_send[0].get_seq() < ack:
                    datagram = self.waiting_for_send.pop(0)
                    self.seq += datagram.get_len()
                    self.seq_bias -= datagram.get_len()
                    self.win_idx -= 1
                    self.win_size += min(0.2, 2 / self.win_size)

                if self.waiting_for_send:
                    self.set_timer(self.waiting_for_send[0])
        else:
            self.duplicate_cnt += 1
            if self.duplicate_cnt == (2 if self.win_size < 3 else 3):
                return False

        return True

    def resend(self, datagram: Datagram, timeout: bool, cnt=0):

        if datagram.is_syn():
            return
        elif datagram.is_fin():
            self.fin_resend_callback(datagram, cnt)
            return

        if datagram.get_seq() < self.seq:
            return
        elif datagram.get_seq() == self.seq:
            datagram.update(seqack=self.seqack)
            self._send(datagram)

            # congestion control
            if not timeout:
                print("Resend due to duplicate ack!")
                self.win_size -= self.win_size / 10
            else:
                print("Resend due to time out!")
                if cnt >= 2:
                    self.win_size = 1
                else:
                    self.win_size -= self.win_size / (3 - cnt)

        self.set_timer(datagram, cnt=cnt + 1)

    def set_timer(self, datagram, cnt=0):
        rto = self.RTO * (cnt * 0.5 + 1)

        seq = datagram.get_seq()
        if datagram.is_syn() or datagram.is_fin():
            # syn/fin 超时，重发
            Timer(rto, self.resend, [datagram, True, cnt]).start()
        else:
            # 数据超时重发
            if seq in self.timers:
                self.timers[seq].cancel()
            self.timers[seq] = Timer(rto, self.resend, [datagram, True, cnt])
            self.timers[seq].start()

    def fin_resend_callback(self, datagram: Datagram, cnt):
        if self.status != Status.Active_fin1 or self.status != Status.Passive_fin2:
            return
        if cnt > 5:
            self.fin_ack_callback()
        else:
            self._send(datagram)
            self.set_timer(datagram=datagram, cnt=cnt + 1)


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""
