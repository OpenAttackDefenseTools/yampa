from enum import Enum
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

class FilterEngine:
    async def filter(self, metadata, data, flowbits: List[str]) -> PyEffects: ...

async def create_filterengine_from_ruleset(connection) -> FilterEngine: ...
