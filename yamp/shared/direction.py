from enum import Enum


class ProxyDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

    def __invert__(self):
        match self:
            case ProxyDirection.INBOUND:
                return ProxyDirection.OUTBOUND
            case ProxyDirection.OUTBOUND:
                return ProxyDirection.INBOUND


class ConnectionDirection(Enum):
    TO_SERVER = "to_server"
    TO_CLIENT = "to_client"

    def __invert__(self):
        match self:
            case ConnectionDirection.TO_SERVER:
                return ConnectionDirection.TO_CLIENT
            case ConnectionDirection.TO_CLIENT:
                return ConnectionDirection.TO_SERVER
