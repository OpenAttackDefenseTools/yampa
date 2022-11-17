import asyncio
import signal

import mitmproxy_wireguard as wireguard

from .config import load_config


async def main():
    config = load_config()

    async def handle_connection(connection: wireguard.TcpStream):
        print(f"Received connection: {connection.get_extra_info('peername')}")
        try:
            data = await connection.read(4096)
            print(f"Read data {data}, returning {data.upper()}...")
        except Exception as exc:
            data = b""

        try:
            connection.write(data.upper())
            await connection.drain()
            connection.close()
        except Exception as exc:
            pass

    def handle_datagram(data, src_addr, dst_addr):
        print(f"Received datagram: {data=} {src_addr=} {dst_addr=}")
        server.send_datagram(data.upper(), dst_addr, src_addr)
        print("Echoed datagram.")

    server = await wireguard.start_server("0.0.0.0", 51820,
                                          config.network.own_private,
                                          [config.network.peer_public],
                                          handle_connection, handle_datagram)

    def stop(*_):
        server.close()

    signal.signal(signal.SIGTERM, stop)

    print(
        f"Server running with own public key {config.network.own_public} and peer public key {config.network.peer_public}")

    await server.wait_closed()


asyncio.run(main())
