import os
from typing import Set, Dict
import logging
import asyncio

from yamp import *

from filter_engine import *


def constructor():
    rules = ""
    with os.scandir("./rules") as scanner:
        for candidate in scanner:
            if candidate.is_file() and not candidate.name.startswith(".") and candidate.name.endswith(".rls"):
                with open(candidate) as f:
                    rules += f.read() + "\n"

    return FilterEnginePlugin(rules)


logger = logging.getLogger(__name__)


class FilterEnginePlugin(PluginBase):
    BUFFER_SIZE = 4096

    def __init__(self, rules: str) -> None:
        super().__init__()

        async def init_engine(r):
            return await create_filterengine_from_ruleset(r)

        self.engine = asyncio.create_task(init_engine(rules))
        self.udp_conns: dict[tuple[str, int, str, int], Dict[ProxyDirection, bytes]] = {}
        self.flow_bits: dict[ProxyConnection | tuple[str, int, str, int], Set[str]] = {}

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        self.flow_bits[connection] = set()

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        del self.flow_bits[connection]

    async def _filter(self, connection: ProxyConnection | tuple[str, int, str, int], metadata,
                      context: bytes) -> FilterAction | None:
        engine = await self.engine

        match metadata.direction:
            case ProxyDirection.INBOUND | (ProxyDirection.INBOUND, _):
                pymetadata = PyMetadata(inner_port=metadata.dst_port, outer_port=metadata.src_port,
                                        direction=PyProxyDirection.InBound)
            case ProxyDirection.OUTBOUND | (ProxyDirection.OUTBOUND, _):
                pymetadata = PyMetadata(inner_port=metadata.src_port, outer_port=metadata.dst_port,
                                        direction=PyProxyDirection.OutBound)
            case _:
                pymetadata = PyMetadata(0, 0, PyProxyDirection.InBound)

        effect = await engine.filter(pymetadata, context, list(self.flow_bits[connection]))

        [self.flow_bits[connection].add(bit) for bit in effect.flow_sets]

        if effect.action is None:
            return None

        logger.info(
            f"Packet in connection {connection}: Action taken: {effect.action}, tagged with {', '.join(effect.tags)}, flowbits {', '.join(effect.flow_sets)}")

        # TODO: write eve.json

        match effect.action.action:
            case PyActionType.Accept:
                return FilterAction.ACCEPT
            case PyActionType.Alert:
                return None
            case PyActionType.Drop:
                return FilterAction.REJECT

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        ret = await self._filter(connection, metadata, context[metadata.direction[0]])
        if ret is not None:
            return ret, data
        else:
            return None

    async def udp_filter(self, metadata: Metadata, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        # Context tracking
        conn_tuple = (metadata.src_ip, metadata.src_port, metadata.dst_ip, metadata.dst_port)
        return_tuple = (metadata.dst_ip, metadata.dst_port, metadata.src_ip, metadata.src_port)
        if conn_tuple in self.udp_conns:
            # seen this connection before, do nothing
            pass
        elif return_tuple in self.udp_conns:
            # this is a response to a seen connection
            conn_tuple = return_tuple
        else:
            # fresh connection
            self.udp_conns[conn_tuple] = {ProxyDirection.INBOUND: b"", ProxyDirection.OUTBOUND: b""}

        self.udp_conns[conn_tuple][metadata.direction] = (self.udp_conns[conn_tuple][metadata.direction] + data)[
                                                         -self.BUFFER_SIZE:]

        ret = await self._filter(conn_tuple, metadata, self.udp_conns[conn_tuple][metadata.direction[0]])
        if ret is not None:
            return ret, data
        else:
            return None
