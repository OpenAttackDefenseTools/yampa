import asyncio
import signal

import mitmproxy_wireguard as wireguard

from .config import load_config


async def handle_connection(forward_server, connection: wireguard.TcpStream):
    # see https://github.com/mitmproxy/mitmproxy/issues/5707 for why this is named like this
    src_addr = connection.get_extra_info('peername')
    dst_addr = connection.get_extra_info('original_dst')

    forward_connection = await forward_server.new_connection(src_addr, dst_addr)

    async def read_forward_task(from_conn: wireguard.TcpStream, to_conn: wireguard.TcpStream):
        while True:
            try:
                data = await from_conn.read(4096)
            except Exception as exc:
                data = b""

            if len(data) == 0:
                to_conn.write_eof()
                from_conn.close()
                return

            side = "network -> proxy" if from_conn == connection else "proxy -> network"
            print(f"{side} {data}")

            try:
                to_conn.write(data)
                await to_conn.drain()
            except Exception as exc:
                pass

    await asyncio.gather(read_forward_task(connection, forward_connection),
                         read_forward_task(forward_connection, connection))


def handle_datagram(forward_server, data, src_addr, dst_addr):
    forward_server.send_datagram(data, dst_addr, src_addr)


async def main():
    config = load_config()

    network_server = await wireguard.start_server("0.0.0.0", 51820,
                                                  config.network.own_private,
                                                  [config.network.peer_public], [config.network.peer_endpoint],
                                                  lambda connection: handle_connection(proxy_server, connection),
                                                  lambda data, src, dst: handle_datagram(proxy_server, data, src, dst))
    proxy_server = await wireguard.start_server("0.0.0.0", 51821,
                                                config.proxy.own_private,
                                                [config.proxy.peer_public], [config.proxy.peer_endpoint],
                                                lambda connection: handle_connection(network_server, connection),
                                                lambda data, src, dst: handle_datagram(network_server, data, src, dst))

    def stop(*_):
        network_server.close()
        proxy_server.close()

    signal.signal(signal.SIGTERM, stop)

    print(
        f"Network server running with own public key {config.network.own_public} and peer public key {config.network.peer_public}")
    print(
        f"Proxy server running with own public key {config.proxy.own_public} and peer public key {config.proxy.peer_public}")

    await asyncio.gather(network_server.wait_closed(), proxy_server.wait_closed())


asyncio.run(main())
