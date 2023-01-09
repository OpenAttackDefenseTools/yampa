import asyncio
import dataclasses
import logging
from asyncio import Task
from typing import TYPE_CHECKING, Any

from .stream import ProxyStream, WrapperStream
from ..shared import Metadata, ConnectionDirection, ProxyDirection, FilterAction

if TYPE_CHECKING:
    from ..plugins import PluginManager

logger = logging.getLogger(__name__)


class ProxyConnection:
    BUFFER_SIZE = 4096

    def __init__(self, pm: "PluginManager", streams: dict[ConnectionDirection, ProxyStream],
                 src_addr: tuple[str, int], dst_addr: tuple[str, int], direction: ProxyDirection):
        self._pm = pm
        self._streams: dict[ConnectionDirection, ProxyStream] = streams
        self._tasks: dict[ConnectionDirection, Task] | None = None
        self._context: dict[ProxyDirection, bytes] = {}
        self._metadata = Metadata(src_addr[0], src_addr[1], dst_addr[0], dst_addr[1], direction)
        self.extra: dict[str, Any] = {}

    def init(self):
        self._tasks = {
            ConnectionDirection.TO_SERVER: asyncio.create_task(self._read_forward_task(ConnectionDirection.TO_SERVER)),
            ConnectionDirection.TO_CLIENT: asyncio.create_task(self._read_forward_task(ConnectionDirection.TO_CLIENT))
        }

    async def wait_closed(self):
        if self._tasks is None:
            self.init()
        await asyncio.gather(*self._tasks.values())

    def wrap(self, streams: dict[ConnectionDirection, WrapperStream]):
        for direction, new_stream in streams.items():
            old_stream = self._streams[direction]
            if old_stream.closing:
                continue

            # Only interrupt if the reading task has already started
            if self._tasks is not None:
                old_stream.interrupt()

            self._streams[direction] = new_stream
            new_stream.stream = old_stream

    @property
    def metadata(self):
        return self._metadata

    async def _read_forward_task(self, to_direction: ConnectionDirection):
        initial_proxy_direction = self._metadata.direction
        proxy_direction = initial_proxy_direction if to_direction == ConnectionDirection.TO_SERVER else ~initial_proxy_direction

        if proxy_direction == initial_proxy_direction:
            metadata = dataclasses.replace(self._metadata, direction=(proxy_direction, to_direction))
        else:
            # If it's a returning packet, also swap src and dst
            metadata = Metadata(self._metadata.dst_ip, self._metadata.dst_port, self._metadata.src_ip,
                                self._metadata.src_port, (proxy_direction, to_direction))

        self._context[proxy_direction] = b""

        while True:
            from_stream = self._streams[~to_direction]
            try:
                data = await from_stream.read(self.BUFFER_SIZE)
                # If read got interrupted, reset the interrupt and start loop again, using new stream
                if from_stream.interrupted:
                    from_stream.reset_interrupt()
                    continue
            except OSError:
                data = b""

            # in case of error or regular close
            if len(data) == 0:
                # write_eof() also closes
                try:
                    self._streams[~to_direction].close(True)
                    self._streams[to_direction].close()
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
                    self._streams[~to_direction].close()
                    self._streams[to_direction].close()
                    return

            data = await self._pm.tcp_encrypt(self, metadata, data)

            side = "net -> pro" if proxy_direction == ProxyDirection.INBOUND else "pro -> net"
            logger.debug(f"[TCP] %s %s", side, data)

            try:
                await self._streams[to_direction].write(data)
            except OSError:
                pass
