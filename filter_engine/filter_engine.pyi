from enum import Enum
from typing import List


class PyAction:
    action: PyActionType
    message: str


class PyActionType(Enum):
    Accept = 1,
    Alert = 2,
    Drop = 3,


class PyMetadata:
    inner_port: int
    outer_port: int
    direction: PyProxyDirection

    def __init__(self, inner_port: int, outer_port: int, direction: PyProxyDirection) -> PyMetadata: ...


class PyProxyDirection(Enum):
    InBound = 1,
    OutBound = 2,


class PyEffects:
    action: PyActionType
    message: str
    tags: List[str]
    flow_sets: List[str]

    def __str__(self) -> str: ...


class FilterEngine:
    async def filter(self, metadata: PyMetadata, data: bytes, flowbits: List[str]) -> PyEffects: ...


async def create_filterengine_from_ruleset(connection) -> FilterEngine: ...
