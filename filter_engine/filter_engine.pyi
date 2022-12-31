from enum import Enum
from dataclasses import dataclass
from typing import List

class PyActionType(Enum):
    Accept = 1,
    Alert = 2
    Drop = 3,

class PyEffects:
    action: PyActionType
    message: str
    tags: List[str]
    flow_sets: List[str]
    def __str__(self) -> str:...


@dataclass()
class ConnectionInfo:
    home_port: str
    dst_port: str
    direction: str


class FilterEngine:
    async def filter(self, metadata: ConnectionInfo, data: List[int], flowbits: List[str]) -> PyEffects: ...

async def create_filterengine_from_ruleset(connection) -> FilterEngine: ...

