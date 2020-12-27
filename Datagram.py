from utils import *

HEADER_LENGTH = 20
DATA_LEN = 1024

class Datagram:
    """
    [0] Flag(1 Byte): ACK, SYN, FIN, END
    [1:5] SEQ (4 Bytes): Sequence num of the data
    [5:9] SEQACK (4 Bytes): Next sequence num of the data should be
    [9:11] LEN (2 Bytes): The length of data in bytes, at most 2^32-1 bytes
    [11:18] Time (7 bytes)
    [18:20] CHECKSUM (2 Bytes): The checksum of the data
    """

    def __init__(self, bytes=None, syn=0, ack=0, fin=0, end=0,
                 seq=0, seqack=0, data=b''):
        if bytes:
            self.header = bytes[:HEADER_LENGTH]
            self.data = bytes[HEADER_LENGTH:]
        else:
            self.header = b''
            flag = (ack << 7) + (syn << 6) + (fin << 5) + (end << 4)
            self.header += num2bytes(flag, length=1)
            self.header += num2bytes(seq, length=4)
            self.header += num2bytes(seqack, length=4)
            self.header += num2bytes(len(data), length=2)
            self.header += time2bytes()
            self.header += get_checksum(self.header, data)
            self.data = data

    def is_ack(self):
        return self.header[0] & 0x80 == 0x80

    def is_syn(self):
        return self.header[0] & 0x40 == 0x40

    def is_fin(self):
        return self.header[0] & 0x20 == 0x20

    def is_end(self):
        return self.header[0] & 0x10 == 0x10

    def get_seq(self):
        return bytes2num(self.header[1:5])

    def get_seqack(self):
        return bytes2num(self.header[5:9])

    def get_len(self):
        return bytes2num(self.header[9:11])

    def get_time(self):
        return self.header[11:18]

    def update(self, seqack=None):
        if seqack:
            new_header = self.header[:5] + num2bytes(seqack, length=4) + self.header[9:11]
        else:
            new_header = self.header[:11]
        new_header = new_header + time2bytes()
        new_header = new_header + get_checksum(new_header, self.data)
        self.header = new_header

    def get_checksum(self):
        return self.header[HEADER_LENGTH-2:HEADER_LENGTH]

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
