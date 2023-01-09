from ..shared import Metadata, FilterAction, ProxyDirection
from ..proxy import ProxyConnection


class PluginBase:
    """This is the base class for plugins. A plugin is defined as any module located in the plugins folder exporting the
    following API:

        def constructor() -> PluginBase: ...

    This constructor is called every time a plugin is loaded or reloaded, and should be used to load and initialize the
    plugin and return a direct subclass of this class. Deeper inheritance patterns are currently not supported, as hooks
    will only be called, if the hook is defined in the `__dict__` of the instance returned by the constructor.
    See `Plugin.__getattribute__` for details on this implementation.

    Make sure that the plugin can generate all its internal state from scratch, as re-using previous versions of objects
    after a plugin reload is a common source of errors. If needed, persist state using `ProxyConnection.extra` but make
    sure not to persist custom datatypes in it.

    A plugin defines its hooks by overriding any of the base functions specified here. There is no need to call
    `super()`, as the function implementations here are only the default implementations used if no plugin exposes a
    given hook.
    """

    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        """This hook is called every time an incoming connection is opened from either side of the proxy. Use it to
        manage internal state for tracking connections.

        Note that this hook is also called once for every currently active connection when the plugin is (re)loaded.
        If you use this to `wrap` a connection, make sure to also save a marker in `connection.extra` to avoid
        double-wrapping connections, as existing wrappers will not be removed on plugin unload.

        :param connection: The incoming tcp connection. Here is where you want to call `ProxyConnection.wrap` if you
            need to take full control over anything that is read or written to this connection.
        :type connection: ProxyConnection
        """
        pass

    async def tcp_connection_closed(self, connection: ProxyConnection) -> None:
        """This hook is called every time an incoming connection is closed. Use this to clean up any internal state.

        :param connection: The tcp connection
        :type connection: ProxyConnection
        """
        pass

    async def tcp_decrypt(self, connection: ProxyConnection, metadata: Metadata, data: bytes) -> None | bytes:
        """This hook is called in the decrypt stage of any tcp connection.

        :param connection: The tcp connection
        :type connection: ProxyConnection
        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always a tuple out of
            ProxyDirection and ConnectionDirection, indicating both whether this packet is coming from the gamenet
            (`INBOUND`) and whether it is sent by the tcp client (`TO_SERVER`) or server (`TO_CLIENT`). Use this to
            decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The bytes read from the connection
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can decrypt the given `data` and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data

    async def tcp_filter(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                         context: dict[ProxyDirection, bytes]) -> None | tuple[FilterAction, bytes | None]:
        """This hook is called in the filter stage of any tcp connection.

        :param connection: The tcp connection
        :type connection: ProxyConnection
        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always a tuple out of
            ProxyDirection and ConnectionDirection, indicating both whether this packet is coming from the gamenet
            (`INBOUND`) and whether it is sent by the tcp client (`TO_SERVER`) or server (`TO_CLIENT`). Use this to
            decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as returned from the decrypt stage
        :type data: bytes
        :param context: Previous traffic for both directions of the connection, currently any previous traffic up to
            4096 bytes. Use this to match based on context, to also match across packet boundaries.
        :type context: dict[ProxyDirection, bytes]
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. Otherwise, a
            tuple should be returned, specifying the taken FilterAction, and the data that should be passed on to the
            next stage. REJECT will close the connection immediately, discarding this packet. ACCEPT will forward the
            returned data in place of the original data to the encrypt stage. Unless None is returned here, no further
            plugin will be called for the filter stage.
        :rtype: None | tuple[FilterAction, bytes | None]
        """
        return None

    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        """This hook is called in the log stage of any tcp connection.

        :param connection: The tcp connection
        :type connection: ProxyConnection
        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always a tuple out of
            ProxyDirection and ConnectionDirection, indicating both whether this packet is coming from the gamenet
            (`INBOUND`) and whether it is sent by the tcp client (`TO_SERVER`) or server (`TO_CLIENT`). Use this to
            decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as returned from the decrypt stage
        :type data: bytes
        :param action: The action taken by the filter stage. Use this if you'd like to log the actions taken by filter
            plugins, or to produce a diff between what went into the filter stage (`data`) and what came out
            (`action[1]`).
        :type action: None | tuple[FilterAction, bytes | None]
        """
        pass

    async def tcp_encrypt(self, connection: ProxyConnection, metadata: Metadata, data: bytes) -> None | bytes:
        """This hook is called in the encrypt stage of any tcp connection.

        :param connection: The tcp connection
        :type connection: ProxyConnection
        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always a tuple out of
            ProxyDirection and ConnectionDirection, indicating both whether this packet is coming from the gamenet
            (`INBOUND`) and whether it is sent by the tcp client (`TO_SERVER`) or server (`TO_CLIENT`). Use this to
            decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as passed on from the filter stage
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can encrypt the given `data` and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data

    async def udp_decrypt(self, metadata: Metadata, data: bytes) -> None | bytes:
        """This hook is called in the decrypt stage of any udp packet.

        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always just ProxyDirection,
            indicating whether this packet is coming from the gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
            Use this to decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The bytes in this packet
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can decrypt the given packet and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data

    async def udp_filter(self, metadata: Metadata, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        """This hook is called in the filter stage of any udp packet.

        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always just ProxyDirection,
            indicating whether this packet is coming from the gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
            Use this to decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as returned from the decrypt stage
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. Otherwise, a
            tuple should be returned, specifying the taken FilterAction, and the data that should be passed on to the
            next stage. REJECT will close the connection immediately, discarding this packet. ACCEPT will forward the
            returned data in place of the original data to the encrypt stage. Unless None is returned here, no further
            plugin will be called for the filter stage.
        :rtype: None | tuple[FilterAction, bytes | None]
        """
        return None

    async def udp_log(self, metadata: Metadata, data: bytes, action: None | tuple[FilterAction, bytes | None]) -> None:
        """This hook is called in the log stage of any udp packet.

        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always just ProxyDirection,
            indicating whether this packet is coming from the gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
            Use this to decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as returned from the decrypt stage
        :type data: bytes
        :param action: The action taken by the filter stage. Use this if you'd like to log the actions taken by filter
            plugins, or to produce a diff between what went into the filter stage (`data`) and what came out
            (`action[1]`).
        :type action: None | tuple[FilterAction, bytes | None]
        """
        pass

    async def udp_encrypt(self, metadata: Metadata, data: bytes) -> None | bytes:
        """This hook is called in the encrypt stage of any udp packet.

        :param metadata: The metadata of this packet. For this hook, `metadata.direction` is always just ProxyDirection,
            indicating whether this packet is coming from the gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
            Use this to decide whether this traffic interests your plugin.
        :type metadata: Metadata
        :param data: The packet bytes, as passed on from the filter stage
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can encrypt the given `data` and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data

    async def other_decrypt(self, direction: ProxyDirection, data: bytes) -> None | bytes:
        """This hook is called in the decrypt stage of any other packet. Other packets are packets that match neither
        IPv4 nor IPv6 TCP / UDP.

        :param direction: The direction this packet is travelling, indicating whether this packet is coming from the
            gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
        :type direction: ProxyDirection
        :param data: The raw bytes in this packet as decrypted from the wireguard stream. This will typically include an
            IP header, it is up to the plugin to parse this.
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can decrypt the given packet and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data

    async def other_filter(self, direction: ProxyDirection, data: bytes) -> None | tuple[FilterAction, bytes | None]:
        """This hook is called in the filter stage of any other packet. Other packets are packets that match neither
        IPv4 nor IPv6 TCP / UDP.

        :param direction: The direction this packet is travelling, indicating whether this packet is coming from the
            gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
        :type direction: ProxyDirection
        :param data: The raw bytes in this packet as returned from the decrypt stage.
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. Otherwise, a
            tuple should be returned, specifying the taken FilterAction, and the data that should be passed on to the
            next stage. REJECT will close the connection immediately, discarding this packet. ACCEPT will forward the
            returned data in place of the original data to the encrypt stage. Unless None is returned here, no further
            plugin will be called for the filter stage.
        :rtype: None | tuple[FilterAction, bytes | None]
        """
        return None

    async def other_log(self, direction: ProxyDirection, data: bytes,
                        action: None | tuple[FilterAction, bytes | None]) -> None:
        """This hook is called in the log stage of any other packet. Other packets are packets that match neither
        IPv4 nor IPv6 TCP / UDP.

        :param direction: The direction this packet is travelling, indicating whether this packet is coming from the
            gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
        :type direction: ProxyDirection
        :param data: The raw bytes in this packet as returned from the decrypt stage.
        :type data: bytes
        :param action: The action taken by the filter stage. Use this if you'd like to log the actions taken by filter
            plugins, or to produce a diff between what went into the filter stage (`data`) and what came out
            (`action[1]`).
        :type action: None | tuple[FilterAction, bytes | None]
        """
        pass

    async def other_encrypt(self, direction: ProxyDirection, data: bytes) -> None | bytes:
        """This hook is called in the encrypt stage of any other packet. Other packets are packets that match neither
        IPv4 nor IPv6 TCP / UDP.

        :param direction: The direction this packet is travelling, indicating whether this packet is coming from the
            gamenet (`INBOUND`) or leaving the proxy (`OUTBOUND`).
        :type direction: ProxyDirection
        :param data: The raw bytes in this packet as passed on from the filter stage.
        :type data: bytes
        :returns: None if this plugin takes no action and the next plugin in the chain should be called. If the plugin
            can encrypt the given `data` and wishes to skip the rest of the pipeline, return a `bytes` object. If all
            plugins return None, `data` is instead used.
        :rtype: None | bytes
        """
        return data
