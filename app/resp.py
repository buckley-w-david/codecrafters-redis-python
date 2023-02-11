import asyncio
from typing import Protocol, Any

class InvalidEncodingError(Exception):
    pass

class RespObject(Protocol):
    data: Any 

    def encode(self) -> bytes:
        ...

    @classmethod
    async def decode(cls, reader: asyncio.StreamReader) -> 'RespObject':
        ...

class SimpleString:
    def __init__(self, data: bytes):
        self.data = data

    def encode(self) -> bytes:
        return b'+%s\r\n' % self.data

    @classmethod
    async def decode(cls, reader: asyncio.StreamReader) -> 'SimpleString':
        s = await reader.readuntil(b"\r\n")
        return SimpleString(s[:-2])

class Error(SimpleString):
    pass

class Integer:
    def __init__(self, data: int):
        self.data = data

    def encode(self) -> bytes:
        ...

    @classmethod
    async def decode(cls, reader: asyncio.StreamReader) -> 'Integer':
        i = await reader.readuntil(b"\r\n")
        return Integer(int(i[:-2]))

class BulkString:
    def __init__(self, data: bytes):
        self.data = data

    def encode(self) -> bytes:
        return b'$%d\r\n%s\r\n' % (len(self.data), self.data)

    @classmethod
    async def decode(cls, reader: asyncio.StreamReader) -> 'BulkString':
        # FIXME: Does this need to be able to handle nulls?
        i = await reader.readuntil(b"\r\n")
        length = int(i[:-2])
        s = await reader.readexactly(length)
        # Throw away ending \r\n
        await reader.readexactly(2)
        return BulkString(s)

class _NullBulkString(BulkString):
    def __init__(self):
        pass

    def encode(self) -> bytes:
        return b'$-1\r\n'

    @classmethod
    async def decode(cls, _reader: asyncio.StreamReader) -> '_NullBulkString':
        raise NotImplementedError
NULL = _NullBulkString()

class Array:
    def __init__(self, data: list[RespObject]):
        self.data = data

    def encode(self) -> bytes:
        return b'*%d\r\n%s' % (len(self.data), b"\r\n".join(obj.encode() for obj in self.data))

    @classmethod
    async def decode(cls, reader: asyncio.StreamReader) -> 'Array':
        i = await reader.readuntil(b"\r\n")
        length = int(i[:-2])

        elements = []
        for _ in range(length):
            elem = await decode(reader)
            elements.append(elem)
        return Array(elements)

async def decode(reader: asyncio.StreamReader) -> RespObject:
    # FIXME: This is a little gross
    type = await reader.readexactly(1)
    if type == b"+":
        return await SimpleString.decode(reader)
    elif type == b"-":
        return await Error.decode(reader)
    elif type == b":":
        return await Integer.decode(reader)
    elif type == b"$":
        return await BulkString.decode(reader)
    elif type == b"*":
        return await Array.decode(reader)
    raise InvalidEncodingError
