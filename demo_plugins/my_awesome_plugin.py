from yampa import *
import logging


def constructor():
    return MyAwesomePlugin()


logger = logging.getLogger(__name__)


class MyAwesomePlugin(PluginBase):
    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        logger.info(f"[TCP] {metadata.direction}: {data}")

    async def udp_log(self, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        logger.info(f"[UDP] {metadata.direction} {metadata.src_ip}:{metadata.src_port} -> {metadata.dst_ip}:{metadata.dst_port}: {data}")

    async def other_log(self, direction: ProxyDirection, data: bytes,
                        action: None | tuple[FilterAction, bytes | None]) -> None:
        logger.info(f"[???] {direction}: {data}")
