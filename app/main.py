import asyncio

from . import command
from . import resp

async def handler(reader, writer):
    while True:
        data = await reader.read(1024) # FIXME: fixed length is wrong
        if not data:
            break
        cmd, _ = resp.Array.decode(data)
        response = await command.exec(cmd)
        writer.write(response.encode())
        await writer.drain()
    writer.close()
    await writer.wait_closed()

async def redis_server():
    server = await asyncio.start_server(handler, host="localhost", port=6379, reuse_port=True)
    async with server:
        await server.serve_forever()

def main():
    asyncio.run(redis_server())

if __name__ == "__main__":
    main()
