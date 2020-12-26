from utils import *

HEADER_LENGTH = 30
DATA_LEN = 1024

class Datagram:
    """
    [0] Flag(1 Byte): ACK, SYN, FIN,...
    [1:9] SEQ (8 Bytes): Sequence num of the data
    [9:17] SEQACK (8 Bytes): Next sequence num of the data should be
    [17:21] LEN (4 Bytes): The length of data in bytes, at most 2^32-1 bytes
    [21:28] Time (7 bytes)
    [28:30] CHECKSUM (2 Bytes): The checksum of the data
    """

    def __init__(self, bytes=None, syn=0, ack=0, fin=0, psh=0, end=0,
                 seq=0, seqack=0, data=b'', time=None):
        if bytes:
            self.header = bytes[:HEADER_LENGTH]
            self.data = bytes[HEADER_LENGTH:]
        else:
            self.header = b''
            flag = (ack << 7) + (syn << 6) + (fin << 5) + (psh << 4) + (end << 3)
            self.header += num2bytes(flag, length=1)
            self.header += num2bytes(seq, length=8)
            self.header += num2bytes(seqack, length=8)
            self.header += num2bytes(len(data), length=4)
            self.header += time if time else time2bytes()
            self.header += get_checksum(self.header, data)
            self.data = data

    def is_ack(self):
        return self.header[0] & 0x80 == 0x80

    def is_syn(self):
        return self.header[0] & 0x40 == 0x40

    def is_fin(self):
        return self.header[0] & 0x20 == 0x20

    def is_psh(self):
        return self.header[0] & 0x10 == 0x10

    def is_end(self):
        return self.header[0] & 0x08 == 0x08

    def get_seq(self):
        return bytes2num(self.header[1:9])

    def get_seqack(self):
        return bytes2num(self.header[9:17])

    def get_len(self):
        return bytes2num(self.header[17:21])

    def get_time(self):
        return self.header[21:28]

    def update(self, seqack=None):
        if seqack:
            new_header = self.header[0:9] + num2bytes(seqack, length=8) + self.header[17:21]
        else:
            new_header = self.header[:21]
        new_header = new_header + time2bytes()
        new_header = new_header + get_checksum(new_header, self.data)
        self.header = new_header

    def get_checksum(self):
        return self.header[28:30]

    def to_bytes(self):
        return self.header + self.data

    def check(self):
        if len(self.header) != HEADER_LENGTH:
            print("Length Error!")
            return False
        if len(self.data) != self.get_len():
            print("Total Length Error!")
            return False
        if self.get_checksum() != get_checksum(self.header[:HEADER_LENGTH-2], self.data):
            print("Checksum Error!")
            return False
        return True

    def __str__(self):
        result = ""
        if self.is_syn(): result += "SYN "
        if self.is_fin(): result += "FIN "
        if self.is_ack(): result += "ACK "
        if self.is_end(): result += "END "
        result += "{seq: %d seqack: %d len: %d}\r\n" % (self.get_seq(), self.get_seqack(), self.get_len())
        return result
