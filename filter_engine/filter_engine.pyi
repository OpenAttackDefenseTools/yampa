from enum import Enum
from dataclasses import dataclass
from typing import List

from .connection_info import ConnectionInfo

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

class FilterEngine:
    async def filter(self, metadata: ConnectionInfo, data: bytes, flowbits: List[str]) -> PyEffects: ...

async def create_filterengine_from_ruleset(connection) -> FilterEngine: ...

