from dataclasses import dataclass

@dataclass()
class ConnectionInfo:
    home_port: str
    dst_port: str
    direction: str

