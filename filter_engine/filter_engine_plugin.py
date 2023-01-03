from typing import Set
from filter_engine.filter_engine import PyActionType
from yamp import *
import logging
import asyncio

from connection_info import ConnectionInfo
from filter_engine import create_filterengine_from_ruleset

def constructor():
    with open('./filter_rules.rls') as f:
        rules = f.read()

    return FilterEnginePlugin(rules)


logger = logging.getLogger(__name__)


class FilterEnginePlugin(PluginBase):
    def __init__(self, rules: str) -> None:
        super().__init__() 
    
        self.rules = rules
        self.engine_task= asyncio.create_task(create_filterengine_from_ruleset(rules))
        self.engine = None
        self.flow_bits: dict[ProxyConnection, Set[str]]

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        logger.info("New connection %s", connection)

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        global logger

        if not self.engine:
            self.engine = await self.engine_task

        logger.info("Filter with context %s", context)
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
        effect = await self.engine.filter(c, data, [])

        if not connection in self.flow_bits:
            self.flow_bits[connection] = set()

        [self.flow_bits[connection].add(bit) for bit in effect.flow_sets]

        action = FilterAction.REJECT
        match effect.action:
            case PyActionType.Alert:
                action = FilterAction.ALERT
            case PyActionType.Accept:
                action = FilterAction.ACCEPT
        
        logger.info(f"Packet in connection {connection}: Action taken: {action}{'with message ' + effect.message if effect.message else ''}, tagged with {', '.join(effect.tags)}")

        return (action, data)

    # async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
    #     return FilterAction.REJECT, None

