import os
from typing import Set
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
    def __init__(self, rules: str) -> None:
        super().__init__()

        async def init_engine(r):
            return await create_filterengine_from_ruleset(r)

        self.engine = asyncio.create_task(init_engine(rules))
        self.flow_bits: dict[ProxyConnection, Set[str]] = {}

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        self.flow_bits[connection] = set()

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        del self.flow_bits[connection]

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        engine = await self.engine

        match metadata.direction[0]:
            case ProxyDirection.INBOUND:
                pymetadata = PyMetadata(inner_port=metadata.dst_port, outer_port=metadata.src_port,
                                        direction=PyProxyDirection.InBound)
            case ProxyDirection.OUTBOUND:
                pymetadata = PyMetadata(inner_port=metadata.src_port, outer_port=metadata.dst_port,
                                        direction=PyProxyDirection.OutBound)
            case _:
                pymetadata = PyMetadata(0, 0, PyProxyDirection.InBound)

        effect = await engine.filter(pymetadata, context[metadata.direction[0]], list(self.flow_bits[connection]))

        [self.flow_bits[connection].add(bit) for bit in effect.flow_sets]

        if effect.action is None:
            return None

        # TODO: write eve.json
        logger.info(
            f"Packet in connection {connection}: Action taken: {effect.action}{' with message ' + effect.message if effect.message else ''}, tagged with {', '.join(effect.tags)}")

        match effect.action:
            case PyActionType.Accept:
                return FilterAction.ACCEPT, data
            case PyActionType.Alert:
                return None
            case PyActionType.Drop:
                return FilterAction.REJECT, None

    # async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
    #     return FilterAction.REJECT, None
