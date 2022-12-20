from dataclasses import dataclass

from .direction import ProxyDirection, ConnectionDirection


@dataclass
class Metadata:
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    direction: ProxyDirection | tuple[ProxyDirection, ConnectionDirection]
