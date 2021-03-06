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

        # 线程相关
        self.send_queue = SimpleQueue()
        self.send_thread = None
        self.recv_queue = SimpleQueue()
        self.recv_thread = None
        self.recv_data_buffer = [b'']
        self.process_thread = None
        self.fin_thread = None
        self.timers = {}
        self.send_datagram_buf = {}
        self.recv_datagram_buf = {}

        # 收发记录
        self.ack_cnt = 0
        self.data_cnt = 0
        self.seq = -1
        self.seqack = -1

        # 记录窗口状态
        self.start_idx, self.bias = 0, 0
        self.win_size, self.data_len = 5, 1024
        self.win_threshold = 16

        # 记录系统状态
        self.isSending = 0
        self.status = Status.Closed

        # 用于设置超时时间
        self.SRTT = 0
        self.DevRTT = 0
        self.RTO = 3
        self.RTT_buf = []
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def thread_start(self):
        self.status = Status.Active

        self.send_thread = Thread(target=self.send_threading)
        self.send_thread.start()
        self.recv_thread = Thread(target=self.recv_threading)
        self.recv_thread.start()
        self.process_thread = Thread(target=self.process_threading)
        self.process_thread.start()

    def send_threading(self):
        while True:
            if self.send_queue.empty():
                time.sleep(0.0001)
            else:
                data = self.send_queue.get()
                self.sendto(data, self.dst_addr)
                # print("Window size: ", self.win_size, "Threshold: ", self.win_threshold)
                print("Send: ", str(Datagram(data)))

            time.sleep(0.00001)
            if self.send_queue.empty() and self.status == Status.Closed:
                break

    def recv_threading(self):
        self.settimeout(3)
        while True:
            try:
                recv_data, address = self.recvfrom(8192)
            except Exception:
                if self.status == Status.Closed:
                    break
                continue
            if address == self.dst_addr:
                self.recv_queue.put(recv_data)

    def process_threading(self):
        while True:
            while self.recv_queue.empty() and self.status != Status.Closed:
                time.sleep(0.0001)

            if self.status == Status.Closed:
                break

            recv_data = Datagram(self.recv_queue.get())
            print("Receive: ", str(recv_data))
            if not recv_data.check():
                self._send(Datagram(ack=1, seq=self.seq, seqack=self.seqack, time=recv_data.get_time()))
                continue

            if recv_data.is_fin():
                if recv_data.is_ack():
                    self.recv_fin_ack()
                else:
                    self.fin_thread = Thread(target=self.recv_fin)
                    self.fin_thread.start()
            elif recv_data.is_syn():
                pass
            elif recv_data.is_ack():
                RTT = time.time() - bytes2time(recv_data.get_time())
                self.update_RTT(RTT)
                # print("RTT: ", RTT, "RTO: ", self.RTO)

                if recv_data.get_seqack() > self.seq:
                    self.move_window(recv_data.get_seqack())
                elif recv_data.get_seqack() == self.seq:
                    # duplicate ack
                    self.ack_cnt += 1
                    if self.ack_cnt == 3:
                        datagram = self.send_datagram_buf[self.seq]
                        self.timers[datagram.get_seq()].cancel()
                        self.resend(datagram, False, cnt=0)
                        self.ack_cnt = 0

            else:
                self.send_data_ack(recv_data)

    def move_window(self, seqack):
        t = seqack - self.seq
        self.seq = seqack

        if t % self.data_len != 0:
            self.bias = 0
        else:
            step = t // self.data_len
            self.bias -= step

            # congestion control
            if self.win_size > self.win_threshold:
                self.win_size += (1 / int(self.win_size)) * step
            else:
                self.win_size += step
                if self.win_size > self.win_threshold > 0:
                    self.win_size = self.win_threshold + self.win_size / int(self.win_threshold) - 1

        self.start_idx += t
        self.ack_cnt = 0

        # update send buffer
        out = []
        for e in self.send_datagram_buf.keys():
            if e < self.seq:
                out.append(e)
        for e in out:
            self.send_datagram_buf.pop(e)

    def update_RTT(self, RTT):
        self.SRTT = self.SRTT + 0.125 * (RTT - self.SRTT)
        self.DevRTT = 0.75 * self.DevRTT + 0.25 * abs(RTT - self.SRTT)
        self.RTO = 1 * self.SRTT + 4 * self.DevRTT

    def recv_fin_ack(self):
        if self.status == Status.Active_fin1:
            self.status = Status.Active_fin2
        elif self.status == Status.Passive_fin2:
            self.status = Status.Closed
            print("Connection Closed!")

    def recv_fin(self):
        while self.isSending:
            time.sleep(0.00001)

        self._send(Datagram(fin=1, ack=1))

        if self.status == Status.Active_fin2:
            while not self.send_queue.empty() and not self.recv_queue.empty():
                time.sleep(0.001)

            self.status = Status.Closed
            print("Connection Closed!")
        elif self.status == Status.Active:
            self.status = Status.Passive_fin1

            while self.isSending:
                time.sleep(0.001)

            datagram = Datagram(fin=1)
            self._send(datagram)
            self.set_timer(seq=-1, datagram=datagram)
            self.status = Status.Passive_fin2

    def send_data_ack(self, datagram: Datagram):
        if self.seqack > datagram.get_seq():
            self.data_cnt += 1
            if self.data_cnt == 2:
                self._send(Datagram(ack=1, seq=self.seq, seqack=self.seqack, time=datagram.get_time()))
                self.data_cnt = 0
        # elif self.seqack < datagram.get_seq():
        #     # store
        #     self.recv_datagram_buf[datagram.get_seq()] = datagram
        #     # send current ack
        #     self._send(Datagram(ack=1, seq=self.seq, seqack=self.seqack, time=datagram.get_time()))
        else:
            self.data_cnt = 0
            self.recv_datagram_buf[datagram.get_seq()] = datagram
            time_temp = datagram.get_time()
            # get the previous received data from buffer
            while self.seqack in self.recv_datagram_buf:
                datagram = self.recv_datagram_buf.pop(self.seqack)
                self.recv_data_buffer[-1] = self.recv_data_buffer[-1] + datagram.data
                self.seqack = datagram.get_seq() + datagram.get_len()
                if datagram.is_end():
                    break

            self._send(Datagram(ack=1, seq=self.seq, seqack=self.seqack, time=time_temp))
            if datagram.is_end() and self.seqack == datagram.get_seq() + datagram.get_len():
                self.recv_data_buffer.append(b'')

    def _send(self, d: Datagram):
        self.send_queue.put(d.to_bytes())

    def _recv(self):
        while self.recv_queue.empty():
            time.sleep(0.0001)

        return self.recv_queue.get()

    def set_timer(self, seq, datagram, cnt=0):
        rto = min(5, self.RTO)
        if cnt >= 1:
            rto = rto * (cnt * 0.5 + 1)
        print("Set timeout: ", rto)
        if seq != -1:
            self.timers[seq] = Timer(rto, self.resend, [datagram, True, cnt])
            self.timers[seq].start()
        else:
            Timer(rto, self.resend, [datagram, True, cnt]).start()

    def resend(self, datagram: Datagram, timeout=True, cnt=0):
        if datagram.is_fin():
            if self.status != Status.Active_fin1 or self.status != Status.Passive_fin2:
                return
            if cnt == 5:
                self.recv_fin_ack()
            else:
                self._send(datagram)
                self.set_timer(seq=-1, datagram=datagram, cnt=cnt + 1)
            return

        if datagram.get_seq() < self.seq:
            return
        elif datagram.get_seq() == self.seq:
            datagram.update()
            self._send(datagram)

            self.win_threshold = self.win_size // 2
            if not timeout:
                print("Resend due to duplicate ack!")
                self.win_size = self.win_threshold

            else:
                print("Resend due to time out!")
                self.win_size = 1

        self.set_timer(datagram.get_seq(), datagram, cnt=cnt+1)

    # Todo: Loss the synack package
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
        ########################################################### ##################
        self.setblocking(True)

        # TODO: BIND?
        conn.bind(('127.0.0.1', 9999))

        while not addr:
            datagram = None
            while not datagram:
                recv_data, addr = self.recvfrom(1024)
                datagram = Datagram(recv_data)
                if not datagram.check():
                    datagram = None

            if datagram.is_syn():

                conn.dst_addr = addr
                conn.thread_start()

                conn._send_to = conn._send
                conn._recv_from = conn._recv

                conn.seq = random.randint(0, (2 << 32) - 1)
                conn.seqack = datagram.get_seq() + 1
                conn._send(Datagram(syn=1, ack=1, seq=conn.seq, seqack=conn.seqack, time=datagram.get_time()))
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
        self.settimeout(1)
        self.seq = random.randint(0, (2 << 32) - 1)
        send_data = Datagram(syn=1, seq=self.seq, time=time2bytes())
        self.sendto(data=send_data.to_bytes(), addr=address)

        recv_data, addr = Datagram(), None
        while not recv_data.is_syn() or not recv_data.is_ack() or recv_data.get_seqack() != self.seq + 1:
            try:
                datagram, addr = self.recvfrom(1024)
                recv_data = Datagram(datagram)
            except Exception:
                send_data.update()
                self.sendto(data=send_data.to_bytes(), addr=address)

        self.setblocking(True)

        self.seq = recv_data.get_seqack()
        self.seqack = recv_data.get_seq() + 1
        self.dst_addr = addr
        self.thread_start()

        # todo:add initial rtt
        self.SRTT = time.time() - bytes2time(recv_data.get_time())
        self.DevRTT = 0
        self.RTO = 3 * self.SRTT

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
        self.isSending = 1
        self.start_idx, self.bias, final_seq = 0, 0, self.seq + len(bytes)

        while self.seq < final_seq:
            while self.bias < int(self.win_size):
            # while self.bias < 5:
                u = int(self.start_idx + self.bias * self.data_len)
                v = int(u + self.data_len)
                seq = int(self.seq + self.bias * self.data_len)

                if u > len(bytes):
                    break

                # print(self.seq, self.bias, final_seq, u, v)
                datagram = Datagram(seq=seq, seqack=self.seqack, end=(v >= len(bytes)),
                                    data=bytes[u:v], time=time2bytes())

                self.send_datagram_buf[seq] = datagram
                self.set_timer(seq, datagram)
                self._send_to(datagram)
                self.bias += 1

            time.sleep(0.0001)

        print("Send finish!")
        self.isSending = 0
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
        self._send_to = None
        self._recv_from = None

        datagram = Datagram(fin=1)
        self._send(datagram)
        self.set_timer(seq=-1, datagram=datagram)
        self.status = Status.Active_fin1

        while self.status != Status.Closed:
            time.sleep(0.01)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        # super().close()


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""
