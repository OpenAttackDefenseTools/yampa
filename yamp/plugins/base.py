from ..shared import Metadata, FilterAction, ProxyDirection
from ..proxy import ProxyConnection


class PluginBase:
    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        pass

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        pass

    async def tcp_decrypt(self, connection: ProxyConnection, metadata: Metadata, data: bytes) -> None | bytes:
        return data

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        return None

    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        pass

    async def tcp_encrypt(self, connection: ProxyConnection, metadata: Metadata, data: bytes) -> None | bytes:
        return data

    async def udp_decrypt(self, metadata: Metadata, data: bytes) -> None | bytes:
        return data

    async def udp_filter(self, metadata: Metadata, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        return None

    async def udp_log(self, metadata: Metadata, data: bytes, action: None | tuple[FilterAction, bytes | None]) -> None:
        pass

    async def udp_encrypt(self, metadata: Metadata, data: bytes) -> None | bytes:
        return data

    async def other_decrypt(self, direction: ProxyDirection, data: bytes) -> None | bytes:
        return data

    async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        return None

    async def other_log(self, direction: ProxyDirection, data: bytes,
                        action: None | tuple[FilterAction, bytes | None]) -> None:
        pass

    async def other_encrypt(self, direction: ProxyDirection, data: bytes) -> None | bytes:
        return data
