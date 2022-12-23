import asyncio
import logging
import random
from typing import Callable

import mitmproxy_wireguard as wireguard
from scapy.layers.inet import IP, TCP

from yamp import *


def constructor():
    return TrafficDumpPlugin()


logger = logging.getLogger(__name__)

# Configuration

OWN_PRIVATE = "SOusLFmtXzv59EFmPUERPUIRZFGEqqcULRTSqn8jQ18="
OWN_PUBLIC = "ojKVvDv49rVcdLQPBtBGXV5MhtPHXrxkxgbG1lYoRkg="

LISTEN_PORT = 51822

RECEIVER_PRIVATE = "+Ch40+dzh1IvrVfRNA2EIcFtAzaLt9Dtk7wq0Lket20="
RECEIVER_PUBLIC = "pu6zwajDNDp+G7QM5yxYX+BDE2Nj1Os2qcv+ZNZVaWs="

# In case you'd like to ensure a specific endpoint
# RECEIVER_ENDPOINT = "dns or ip address:port"
# If you leave it as None, make sure to have the endpoint connect to this server before attempting to send any data
RECEIVER_ENDPOINT = None


# End Configuration

# A fake tcp connection that allows us to send data "from both sides"
class FakeTcpConnection:
    def __init__(self, metadata: Metadata, send_function: Callable[[bytes], None]):
        self._client = IP(src=metadata.src_ip, dst=metadata.dst_ip) / \
                       TCP(sport=metadata.src_port, dport=metadata.dst_port, flags=0, seq=random.randrange(0, 2 ** 32))
        self._server = IP(src=metadata.dst_ip, dst=metadata.src_ip) / \
                       TCP(sport=metadata.dst_port, dport=metadata.src_port, flags=0, seq=random.randrange(0, 2 ** 32))
        self.send_function = send_function

    def _send(self, packet, other, flags, payload: bytes | None = None):
        packet[TCP].flags = flags
        packet[TCP].ack = other[TCP].seq

        if payload is not None:
            packet[TCP] /= payload
        self.send_function(bytes(packet))

        if payload is not None:
            packet[TCP].seq = (packet[TCP].seq + len(packet[TCP].payload)) % 2 ** 32
            packet[TCP].remove_payload()

    def handshake(self):
        # First syn does not ack
        self._client[TCP].flags = "S"
        self.send_function(bytes(self._client))
        self._client[TCP].seq += 1

        self._send(self._server, self._client, "SA")
        self._server[TCP].seq += 1
        self._send(self._client, self._server, "A")

    def send_data(self, data: bytes, is_client: bool):
        our = self._client if is_client else self._server
        other = self._server if is_client else self._client

        self._send(our, other, "PA", data)
        self._send(other, our, "A")

    def send_close(self):
        self._send(self._client, self._server, "F")
        self._client[TCP].seq += 1
        self._send(self._server, self._client, "FA")
        self._server[TCP].seq += 1
        self._send(self._client, self._server, "A")


class TrafficDumpPlugin(PluginBase):
    def __init__(self):
        self._setup_task = asyncio.create_task(self.setup())
        self._server: wireguard.Server | None = None
        self._connections: dict[ProxyConnection, FakeTcpConnection] = {}

    async def setup(self):
        async def do_nothing(*_):
            pass

        async def handle_connection(connection: wireguard.TcpStream):
            connection.close()

        self._server = await wireguard.start_server("0.0.0.0", LISTEN_PORT,
                                                    OWN_PRIVATE,
                                                    [RECEIVER_PUBLIC],
                                                    [RECEIVER_ENDPOINT],
                                                    handle_connection,
                                                    do_nothing,
                                                    do_nothing)

    async def ensure_setup(self):
        if self._setup_task is not None:
            await self._setup_task
            self._setup_task = None

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        await self.ensure_setup()

        self._connections[connection] = FakeTcpConnection(connection.metadata, self._server.send_other_packet)
        self._connections[connection].handshake()

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        await self.ensure_setup()
        if connection in self._connections:
            stream = self._connections[connection]
            stream.send_close()
            del self._connections[connection]

    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        await self.ensure_setup()
        if connection in self._connections:
            stream = self._connections[connection]
            stream.send_data(data, metadata.direction[1] == ConnectionDirection.TO_SERVER)

    async def udp_log(self, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        await self.ensure_setup()
        self._server.send_datagram(data, (metadata.src_ip, metadata.src_port), (metadata.dst_ip, metadata.dst_port))

    async def other_log(self, direction: ProxyDirection, data: bytes,
                        action: None | tuple[FilterAction, bytes | None]) -> None:
        await self.ensure_setup()
        self._server.send_other_packet(data)
