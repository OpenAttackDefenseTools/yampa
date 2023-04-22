import json
import os
from datetime import datetime
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
        self._eve = None

        async def init_engine(r):
            engine = await create_filterengine_from_ruleset(r)
            self._eve = open("./rules/eve.json", "a")
            return engine

        self.engine = asyncio.create_task(init_engine(rules))
        self.udp_conns: dict[tuple[str, int, str, int], Dict[ProxyDirection, bytes]] = {}
        self.flow_bits: dict[ProxyConnection | tuple[str, int, str, int], Set[str]] = {}
        self.flow_starts: dict[ProxyConnection | tuple[str, int, str, int], str] = {}

    def __del__(self):
        if self._eve is not None:
            self._eve.close()
            self._eve = None

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        # Persist flowbits across plugin reloads
        flowbit_marker = "FILTER_ENGINE_FLOWBITS"
        flowstart_marker = "FILTER_ENGINE_FLOWSTARTS"

        if flowbit_marker not in connection.extra:
            connection.extra[flowbit_marker] = set()

        if flowstart_marker not in connection.extra:
            connection.extra[flowstart_marker] = datetime.utcnow().isoformat() + "+0000"

        self.flow_bits[connection] = connection.extra[flowbit_marker]
        self.flow_starts[connection] = connection.extra[flowstart_marker]

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        del self.flow_bits[connection]
        del self.flow_starts[connection]

    async def _log(self, connection: ProxyConnection | tuple[str, int, str, int], metadata: Metadata, effect: PyEffects):
        # This is a minimal version of suricata's eve.json
        log = {
            "src_ip": metadata.src_ip,
            "src_port": metadata.src_port,
            "dest_ip": metadata.dst_ip,
            "dest_port": metadata.dst_port,
            "flow": {"start": self.flow_starts[connection]},
            "alert": {
                "signature": effect.action.message,
                "signature_id": 0,
                "action": "blocked" if effect.action.action == PyActionType.Drop else "allowed",
                "metadata": {
                    "tag": effect.tags,
                    "flowbits": effect.flow_sets
                }
            }
        }

        self._eve.write(f"{json.dumps(log)}\n")
        self._eve.flush()

    async def _filter(self, connection: ProxyConnection | tuple[str, int, str, int], metadata: Metadata,
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

        await self._log(connection, metadata, effect)

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
            self.flow_bits[conn_tuple] = set()
            self.flow_starts[conn_tuple] = datetime.utcnow().isoformat() + "+0000"

        self.udp_conns[conn_tuple][metadata.direction] = (self.udp_conns[conn_tuple][metadata.direction] + data)[
                                                         -self.BUFFER_SIZE:]

        ret = await self._filter(conn_tuple, metadata, self.udp_conns[conn_tuple][metadata.direction])
        if ret is not None:
            return ret, data
        else:
            return None
