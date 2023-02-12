import enum

import time
from . import resp

def now():
    return time.time_ns() // 1_000_000

class Command(enum.Enum):
    PING = b"PING"
    ECHO = b"ECHO"
    SET  = b"SET"
    GET  = b"GET"

# from typing import Callable, Awaitable
# command = Callable[[int, list[resp.RespObject]], Awaitable[resp.RespObject]]
STORAGE = {}

async def ping(argc: int, argv: list[resp.BulkString]) -> resp.SimpleString:
    return resp.SimpleString(b"PONG")

async def echo(argc: int, argv: list[resp.BulkString]) -> resp.SimpleString:
    return resp.SimpleString(argv[1].data)

async def set(argc: int, argv: list[resp.BulkString]) -> resp.SimpleString | resp.BulkString:
    key = argv[1]
    value = argv[2]
    idx = 3 # skip the required stuff
    old_value, old_expire = None, None
    if key in STORAGE:
        old_value, old_expire = STORAGE[key]

    expire = None
    skip_exists = False
    only_exists = False
    keep_ttl = False
    get = False
    # TODO: Would be nice to have a more generic argument parsing routine
    while idx < len(argv)-1:
        match argv[idx].data.upper():
            case b"PX":
                expire = now() + int(argv[idx+1].data)
                idx += 1
            case b"EX":
                expire = now() + int(argv[idx+1].data)*1000
                idx += 1
            case b"EXAT":
                expire = int(argv[idx+1].data)*1000
                idx += 1
            case b"PXAT":
                expire = int(argv[idx+1].data)
                idx += 1
            case b"NX":
                skip_exists = True
            case b"XX":
                only_exists = True
            case b"KEEPTTL":
                keep_ttl = True
            case b"GET":
                get = True
        idx += 1

    if skip_exists and old_value:
        return resp.NULL
    elif only_exists and not old_value:
        return resp.NULL
    if keep_ttl:
        expire = old_expire

    STORAGE[key.data] = (value, expire)

    if get:
        out = old_value if old_value else resp.NULL
    else:
        out = resp.SimpleString(b"OK")
    return out

async def get(argc: int, argv: list[resp.BulkString]) -> resp.BulkString:
    key = argv[1].data
    if key in STORAGE:
        value, expire = STORAGE[key]
        if expire and now() > expire:
            del STORAGE[key]
            return resp.NULL
        return value
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
