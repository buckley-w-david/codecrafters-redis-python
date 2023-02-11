from typing import Callable, Awaitable
from . import resp
import enum

class Command(enum.Enum):
    PING = b"PING"
    ECHO = b"ECHO"
    SET  = b"SET"
    GET  = b"GET"

# command = Callable[[int, list[resp.RespObject]], Awaitable[resp.RespObject]]
STORAGE = {}

async def ping(argc, argv) -> resp.SimpleString:
    return resp.SimpleString(b"PONG")

async def echo(argc, argv) -> resp.SimpleString:
    return resp.SimpleString(argv[1].data)

async def set(argc, argv) -> resp.SimpleString:
    key = argv[1]
    value = argv[2]

    STORAGE[key.data] = value
    return resp.SimpleString(b"OK")

async def get(argc, argv) -> resp.BulkString:
    key = argv[1].data
    if key in STORAGE:
        return STORAGE[key]
    else:
        return resp.NULL

VTABLE = {
    Command.PING: ping,
    Command.ECHO: echo,
    Command.SET: set,
    Command.GET: get,
}

async def exec(command: resp.Array) -> resp.RespObject:
    cmd = Command(command.data[0].data.upper())
    return await VTABLE[cmd](len(command.data), command.data)
