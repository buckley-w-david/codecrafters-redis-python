import asyncio

from . import command
from . import resp

async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            try:
                await reader.readexactly(1)
                cmd = await resp.Array.decode(reader)
                response = await command.exec(cmd)
            except resp.Error as e:
                response = e
            writer.write(response.encode())
            await writer.drain()
    except Exception:
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
