from yamp import *
import logging
import filter_engine


def constructor():
    return FilterEnginePlugin()


logger = logging.getLogger(__name__)


class FilterEnginePlugin(PluginBase):
    def __init__(self) -> None:
        super().__init__() rule = 'ACCEPT("hello") FLOWS("asdf") TAGS("hello") : OUT(8080) : "FLAG\{[A-Za-z0-9]+\}" SET("asdf");' self.engine = await filter_engine.create_filterengine_from_ruleset(rule)

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        logger.info("New connection %s", connection)

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        logger.info("Filter with context %s", context)

        if b"AAAAAAA" in context[ProxyDirection.INBOUND]:
            return FilterAction.REJECT, None

        if b"flag" in context[ProxyDirection.OUTBOUND]:
            return FilterAction.ACCEPT, b"notflag\n"

        return None

    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        logger.info("Logging data %s and action %s", data, action)

    # async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
    #     return FilterAction.REJECT, None

