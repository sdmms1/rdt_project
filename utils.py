import time

def get_checksum(data1, data2=b''):
    data = data1 + data2
    result = sum(data[i] << (8 * (i % 2)) for i in range(len(data))) & 0xffff
    return num2bytes(result, length=2)


def bytes2num(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=False)


def num2bytes(num, length=8):
    return int.to_bytes(num, length=length, byteorder='big', signed=False)

def time2bytes():
    t = time.time() * 1000000
    return num2bytes(int(t), 7)

def bytes2time(t):
    t = bytes2num(t)
    return t / 1000000


if __name__ == '__main__':
    # num = 1024
    # a = num2bytes(num)
    # print(a)
    # b = bytes2num(a)
    # print(b)
    # print((1 << 7) + (1 << 6))
    for e in time2bytes():
        print(hex(e))
