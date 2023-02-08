from typing import Protocol, Any

class InvalidEncodingError(Exception):
    pass

class RespObject(Protocol):
    data: Any 

    def encode(self) -> bytes:
        ...

    @classmethod
    def decode(cls, data: bytes) -> tuple['RespObject', int]:
        ...

class SimpleString:
    def __init__(self, data: bytes):
        self.data = data

    def encode(self) -> bytes:
        return b'+%s\r\n' % self.data

    @classmethod
    def decode(cls, data: bytes) -> tuple['SimpleString', int]:
        s, _ = data.split(b"\r\n", 1)
        #                        str + \r\n
        return SimpleString(s[1:]), len(s) + 2

class Error(SimpleString):
    pass

class Integer:
    def __init__(self, data: int):
        self.data = data

    def encode(self) -> bytes:
        ...

    @classmethod
    def decode(cls, data: bytes) -> tuple['Integer', int]:
        s, _ = data.split(b"\r\n", 1)
        return Integer(int(s[1:])), len(s) + 2

class BulkString:
    def __init__(self, data: bytes):
        self.data = data

    def encode(self) -> bytes:
        return b'$%d\r\n%s\r\n' % (len(self.data), self.data)

    @classmethod
    def decode(cls, data: bytes) -> tuple['BulkString', int]:
        prefix, string = data.split(b"\r\n", 1)
        length = int(prefix.decode()[1:])
        #                                   prefix   +  \r\n + string + \r\n
        return BulkString(string[:length]), len(prefix) + 2 + length + 2

NULL = "$-1\r\n"

class Array:
    def __init__(self, data: list[RespObject]):
        self.data = data

    def encode(self) -> bytes:
        return b'*%d\r\n%s' % (len(self.data), b"\r\n".join(obj.encode() for obj in self.data))

    @classmethod
    def decode(cls, data: bytes) -> tuple['Array', int]:
        prefix, data = data.split(b"\r\n", 1)
        length = int(prefix.decode()[1:])

        offset = 0
        elements = []
        for _ in range(length):
            elem, l = decode(data[offset:])
            elements.append(elem)
            offset += l

        return Array(elements), offset + len(prefix) + 2

def decode(data: bytes) -> tuple[RespObject, int]:
    # FIXME: This is a little gross
    if data.startswith(b"+"):
        return SimpleString.decode(data)
    elif data.startswith(b"-"):
        return Error.decode(data)
    elif data.startswith(b":"):
        return Integer.decode(data)
    elif data.startswith(b"$"):
        return BulkString.decode(data)
    elif data.startswith(b"*"):
        return Array.decode(data)
    raise InvalidEncodingError
