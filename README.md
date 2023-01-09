# YAMP -- User Manual

## Overview

YAMP is Yet Another Mitm Proxy for use in A/D CTFs.
It is intended to sit in between the gamenet and vulnbox and can be customized via plugins to perform different functionality on the traffic.

Fun fact: Yamp is also the short name for [various plants native to western North America](https://en.wikipedia.org/wiki/Perideridia).

## Setup

Since YAMP runs in docker, you hardly have to take care of prerequisites -- except for docker, of course.

To setup YAMP, do the following:

1. Clone the repository. (In the rest of the documentantion, `./` refers to the repository.)
2. Follow the comments in `./generate-env.sh` (on lines 30, 39, 118 and 127) to set the key pairs for both sides (gamenet and vulnbox side) of the proxy. This script will provide you with a template environment, which is well-suited for tests, but it may have to be adjusted for your individual requirements during a CTF.
3. Run `./generate-env.sh`. (You will have to re-run this every time you make adjustments to the script.)
4. Set the following environment variables:
	* Set `ENV_FILE` to point to the generated environment file, e.g. `ENV_FILE=".env"`).
	* Set `RULES_DIR` to point to the directory where you want filter rules to be loaded from, e.g. `RULES_DIR="./rules"`
	* Set `PLUGIN_DIR` to point to the directory where you want plugins to be loaded from, e.g. `PLUGIN_DIR="./plugins"`

At this point, YAMP should be ready to run. To start it, use the following command:

```
docker compose up -d
```

## Plugins

When YAMP is started up freshly without any plugins, the proxy will behave transparently. That is, it will forward traffic in both directions without modifying, filtering or logging it. To do so, you will want to add plugins.

A plugin implements multiple hooks. The hooks have the following intended functionality:

* decrypting
* filtering
* logging
* encrypting

You can think of a data packet as walking through these stages in the above order.

When multiple plugins are loaded, the respective hooks of all plugins are executed simultaneously with the same input parameters. Some hooks, like decryption, are meant to return data. Regarding the return value, only the first output that is not `None` is taken and processed further. That is, by returning `None`, a hook can indicate that a certain data packet is `None` of its business.

Find more details on the implementation of plugins in the section "Writing Plugins".


### Loading Plugins

To add your plugins, add them to your specified plugin directory (e.g. `./plugins`). For the changes to take effect during runtime, call `./reload.sh`.

If an old version of a plugin is running and an error arises while loading the newer version, the old version will keep running. That is, plugins are only replaced if at least the load process is successful.

### Writing Plugins

On a technical level, a plugin is a python module (or package) that exposes a function of the following signature:

```
def constructor() -> PluginBase
```

That is, the constructor returns an instance of a subclass of `PluginBase`. You can use the constructor to do some initialization (like loading filter rules from a file).

The class `PluginBase` defines the available hooks and their signatures. To find out what hooks are available, look at `./yamp/plugins/base.py` or the following excerpt:

```
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
```

Each plugin has to implement all of the above hooks. However, by default most of the hook implementations return `None`, which indicates that they should be ignored.

## The Filter Engine

TODO
