import asyncio
import logging
import traceback

import mitmproxy_wireguard as wireguard

from .config import load_config
from .connection import ProxyConnection
from .stream import WireguardStream
from ..shared import FilterAction, ProxyDirection, ConnectionDirection, Metadata

logger = logging.getLogger(__name__)


class Proxy:
    def __init__(self):
        from ..plugins import PluginManager
        self._config = load_config()
        self._pm = PluginManager()
        self._network_server = None
        self._proxy_server = None

    async def start(self):
        # Initial plugin load
        await self._pm.reload()

        self._network_server = await wireguard.start_server("0.0.0.0", 51820,
                                                            self._config.network.own_private,
                                                            [self._config.network.peer_public],
                                                            [self._config.network.peer_endpoint],
                                                            lambda connection: self._handle_connection(
                                                                self._proxy_server, connection),
                                                            lambda data, src, dst: self._handle_datagram(
                                                                self._proxy_server, data, src, dst),
                                                            lambda data: self._handle_other(self._proxy_server, data))

        self._proxy_server = await wireguard.start_server("0.0.0.0", 51821,
                                                          self._config.proxy.own_private,
                                                          [self._config.proxy.peer_public],
                                                          [self._config.proxy.peer_endpoint],
                                                          lambda connection: self._handle_connection(
                                                              self._network_server, connection),
                                                          lambda data, src, dst: self._handle_datagram(
                                                              self._network_server, data, src, dst),
                                                          lambda data: self._handle_other(self._network_server, data))

        logger.info(
            f"Network server running with own public key %s and peer public key %s",
            self._config.network.own_public, self._config.network.peer_public)
        logger.info(
            f"Proxy server running with own public key %s and peer public key %s",
            self._config.proxy.own_public, self._config.proxy.peer_public)

    async def wait_closed(self):
        await asyncio.gather(self._network_server.wait_closed(), self._proxy_server.wait_closed())

    def close(self):
        self._network_server.close()
        self._proxy_server.close()

    async def reload(self):
        await self._pm.reload()

    async def _handle_connection(self, to_server: wireguard.Server, connection: wireguard.TcpStream):
        # see https://github.com/mitmproxy/mitmproxy/issues/5707 for why this is named like this
        src_addr = connection.get_extra_info('peername')
        dst_addr = connection.get_extra_info('original_dst')

        direction = ProxyDirection.INBOUND if to_server == self._proxy_server else ProxyDirection.OUTBOUND

        forward_connection = await to_server.new_connection(src_addr, dst_addr)
        streams = {ConnectionDirection.TO_CLIENT: WireguardStream(connection),
                   ConnectionDirection.TO_SERVER: WireguardStream(forward_connection)}

        connection = ProxyConnection(self._pm, streams, src_addr, dst_addr, direction)
        try:
            await self._pm.tcp_new_connection(connection)
            connection.init()
            await connection.wait_closed()
            await self._pm.tcp_connection_closed(connection)
        except Exception as e:
            logger.error("Error occurred")
            logger.error(traceback.format_exc())

    async def _handle_datagram(self, to_server: wireguard.Server, data, src_addr, dst_addr):
        direction = ProxyDirection.INBOUND if to_server == self._proxy_server else ProxyDirection.OUTBOUND
        metadata = Metadata(src_addr[0], src_addr[1], dst_addr[0], dst_addr[1], direction)

        data = await self._pm.udp_decrypt(metadata, data)

        action = await self._pm.udp_filter(metadata, data)
        await self._pm.udp_log(metadata, data, action)
        if action is not None:
            (action, data) = action
            if action == FilterAction.REJECT:
                return

        data = await self._pm.udp_encrypt(metadata, data)

        side = "net -> pro" if direction == ProxyDirection.INBOUND else "pro -> net"
        logger.debug(f"[UDP] %s %s", side, data)

        to_server.send_datagram(data, dst_addr, src_addr)

    async def _handle_other(self, to_server: wireguard.Server, data):
        direction = ProxyDirection.INBOUND if to_server == self._proxy_server else ProxyDirection.OUTBOUND

        data = await self._pm.other_decrypt(direction, data)

        action = await self._pm.other_filter(direction, data)
        await self._pm.other_log(direction, data, action)
        if action is not None:
            (action, data) = action
            if action == FilterAction.REJECT:
                return

        data = await self._pm.other_encrypt(direction, data)

        side = "net -> pro" if direction == ProxyDirection.INBOUND else "pro -> net"
        logger.debug(f"[???] %s %s", side, data)

        to_server.send_other_packet(data)
