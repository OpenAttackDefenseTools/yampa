import asyncio
import logging
from typing import TYPE_CHECKING

import mitmproxy_wireguard as wireguard

from ..shared import Metadata, ConnectionDirection, ProxyDirection, FilterAction

if TYPE_CHECKING:
    from ..plugins import PluginManager

logger = logging.getLogger(__name__)


class ProxyConnection:
    BUFFER_SIZE = 4096

    def __init__(self, pm: "PluginManager", from_connection: wireguard.TcpStream, to_connection: wireguard.TcpStream,
                 src_addr, dst_addr, direction: ProxyDirection):
        self._pm = pm
        self._from_connection = from_connection
        self._to_connection = to_connection
        self._src_addr = src_addr
        self._dst_addr = dst_addr
        self._direction = direction
        self._from_to_task = asyncio.create_task(self._read_forward_task(self._from_connection, self._to_connection))
        self._to_from_task = asyncio.create_task(self._read_forward_task(self._to_connection, self._from_connection))
        self._context = {}

    async def wait_closed(self):
        await asyncio.gather(self._from_to_task, self._to_from_task)

    async def _read_forward_task(self, from_conn, to_conn):
        proxy_direction = self._direction if from_conn == self._from_connection else ~self._direction
        connection_direction = ConnectionDirection.TO_SERVER if proxy_direction == self._direction else ConnectionDirection.TO_CLIENT

        metadata = Metadata(self._src_addr[0], self._src_addr[1], self._dst_addr[0], self._dst_addr[1],
                            (proxy_direction, connection_direction))

        self._context[proxy_direction] = b""

        while True:
            try:
                data = await from_conn.read(self.BUFFER_SIZE)
            except OSError:
                data = b""

            # in case of error or regular close
            if len(data) == 0:
                # write_eof() also closes
                try:
                    to_conn.write_eof()
                    from_conn.close()
                except OSError:
                    pass
                return

            data = await self._pm.tcp_decrypt(self, metadata, data)

            # Context tracking
            self._context[proxy_direction] = (self._context[proxy_direction] + data)[-self.BUFFER_SIZE:]

            action = await self._pm.tcp_filter(self, metadata, data, self._context)
            await self._pm.tcp_log(self, metadata, data, action)
            if action is not None:
                (action, data) = action
                if action == FilterAction.REJECT:
                    from_conn.close()
                    to_conn.close()
                    return

            data = await self._pm.tcp_encrypt(self, metadata, data)

            side = "net -> pro" if proxy_direction == ProxyDirection.INBOUND else "pro -> net"
            logger.debug(f"[TCP] %s %s", side, data)

            try:
                to_conn.write(data)
                await to_conn.drain()
            except OSError:
                pass
