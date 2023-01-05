import os
from dataclasses import dataclass
from typing import Set
import logging
import asyncio

from yamp import *

from filter_engine import create_filterengine_from_ruleset, PyActionType


@dataclass()
class ConnectionInfo:
    home_port: str
    dst_port: str
    direction: str


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

        c = ConnectionInfo("", "", "")

        match metadata.direction:
            case ProxyDirection.INBOUND | (ProxyDirection.INBOUND, _):
                c.direction = "IN"
                c.home_port = str(metadata.dst_port)
                c.dst_port = str(metadata.src_port)
            case ProxyDirection.OUTBOUND | (ProxyDirection.OUTBOUND, _):
                c.direction = "OUT"
                c.dst_port = str(metadata.dst_port)
                c.home_port = str(metadata.src_port)

        # TODO: add flow bits (Idk who should manage them)
        effect = await engine.filter(c, context[metadata.direction[0]], list(self.flow_bits[connection]))

        [self.flow_bits[connection].add(bit) for bit in effect.flow_sets]

        action = FilterAction.REJECT
        match effect.action:
            case PyActionType.Alert:
                action = FilterAction.ALERT
            case PyActionType.Accept:
                action = FilterAction.ACCEPT

        logger.info(
            f"Packet in connection {connection}: Action taken: {action}{' with message ' + effect.message if effect.message else ''}, tagged with {', '.join(effect.tags)}")

        return action, data

    # async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
    #     return FilterAction.REJECT, None
