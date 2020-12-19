def get_checksum(data1, data2=''):
    data = data1 + data2
    result = sum(data[i] << (8 * (i % 2)) for i in range(len(data))) & 0xffff
    return num2bytes(result, length=2)


def bytes2num(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=False)


def num2bytes(num, length=8):
    return int.to_bytes(num, length=length, byteorder='big', signed=False)


if __name__ == '__main__':
    # num = 1024
    # a = num2bytes(num)
    # print(a)
    # b = bytes2num(a)
    # print(b)
    print((1 << 7) + (1 << 6))
    print(num2bytes(262144))
