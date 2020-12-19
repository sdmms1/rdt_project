from utils import *

HEADER_LENGTH = 23

class Datagram:
    """
    [0] Flag(1 Byte): ACK, SYN, FIN,...
    [1:9] SEQ (8 Bytes): Sequence num of the data
    [9:17] SEQACK (8 Bytes): Next sequence num of the data should be
    [17:21] LEN (4 Bytes): The length of data in bytes, at most 2^32-1 bytes
    [21:23] CHECKSUM (2 Bytes): The checksum of the data
    PAYLOAD (): The length of the header in bytes
    """

    def __init__(self, bytes=None, syn=0, ack=0, fin=0,
                 seq=0, seqack=0, data=b''):
        if bytes:
            self.header = bytes[:HEADER_LENGTH]
            self.data = bytes[HEADER_LENGTH:]
        else:
            # print(seq)
            self.header = b''
            flag = (ack << 7) + (syn << 6) + (fin << 5)
            self.header += num2bytes(flag, length=1)
            self.header += num2bytes(seq, length=8)
            self.header += num2bytes(seqack, length=8)
            self.header += num2bytes(len(data), length=4)
            self.header += get_checksum(self.header, data)

            self.data = data

    def is_ack(self):
        return self.header[0] & 0x80 == 0x80

    def is_syn(self):
        return self.header[0] & 0x40 == 0x40

    def is_fin(self):
        return self.header[0] & 0x20 == 0x20

    def get_seq(self):
        return bytes2num(self.header[1:9])

    def get_seqack(self):
        return bytes2num(self.header[9:17])

    def get_len(self):
        return bytes2num(self.header[17:21])

    def get_checksum(self):
        return self.header[21:23]

    def to_bytes(self):
        return self.header + self.data

    def check(self):
        if len(self.header) != HEADER_LENGTH:
            print("Length Error!")
            return False
        if len(self.data) != self.get_len():
            print("Total Length Error!")
            return False
        if self.get_checksum() != get_checksum(self.header[:21], self.data):
            print("Checksum Error!")
            return False
        return True
