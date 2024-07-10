import re

from yampa import *


def constructor():
    return TestPlugin()


class TestPlugin(PluginBase):
    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        if metadata.dst_port == 80 or metadata.dst_port == 443:
            if b"AAAAAAAAAAAAAAAAAAAAAAA" in data:
                return FilterAction.REJECT, None

        return None

    async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        if direction == ProxyDirection.OUTBOUND and re.search(b"TESTFLAG_[A-Z]{20}", data):
            return FilterAction.REJECT, None
        return None
