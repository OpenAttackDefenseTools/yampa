# YAMP -- User Manual

## Overview

YAMP is Yet Another Mitm Proxy for use in A/D CTFs.
It is intended to sit in between the gamenet and vulnbox and can be customized via plugins to perform different functionality on the traffic.

Fun fact: Yamp is also the short name for [various plants native to western North America](https://en.wikipedia.org/wiki/Perideridia).

## Setup

Since YAMP runs in docker, you hardly have to take care of prerequisites -- except for docker, of course.

To setup YAMP, do the following:

1. Clone the repository. (In the rest of the documentantion, `./` refers to the repository.)
2. Follow the comments in `./generate-env.sh` (on lines 30, 39, 118 and 127) to set the key pairs for both sides (gamenet and vulnbox side) of the proxy.
3. Run `./generate-env.sh`. This will yield a template environment, which is well-suited for tests, but it may have to be adjusted for your individual requirements during a CTF.
4. Optionally, you can obtain more customizability by setting the following environment variables:
	* Set `ENV_FILE` to point to the generated environment file. Default is `ENV_FILE=".env"`).
	* Set `RULES_DIR` to point to the directory where you want filter rules to be loaded from. Default is `RULES_DIR="./rules"`.
	* Set `PLUGIN_DIR` to point to the directory where you want plugins to be loaded from. Default is `PLUGIN_DIR="./plugins"`.

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

When multiple plugins are loaded, the respective hooks of all plugins are executed one after the other with the same input parameters. When a hook returns `None`, the hook of the next plugin in sequence will be called. If a hook returns something different from `None` (for instance, when the decryption hook returns decrypted data), the rest of the chain is dropped and this output will be taken as the output of the chain. This means that by returning `None`, a hook can indicate that a certain data packet is `None` of its business and that the next plugin (if any) should take care of it.

Exception to this are such hooks that don't have a return value, like logging, `tcp_new_connection` and `tcp_connection_close`. For these hooks, the respective implementations of all loaded plugins are executed in parallel.

Find more details on the implementation of plugins in the section "Writing Plugins".


### Loading Plugins

To add your plugins, add them to your specified plugin directory (e.g. `./plugins`). For the changes to take effect during runtime, call `./reload.sh`.

If an old version of a plugin is running and an error arises while loading the newer version, the old version will keep running. That is, plugins are only replaced if at least the load process is successful.

### Writing Plugins

On a technical level, a plugin is a python module (or package) that exposes a function of the following signature:

```
def constructor() -> PluginBase
```

That is, the constructor returns an instance of a *direct* subclass of `PluginBase`. You can use the constructor to do some initialization (like loading filter rules from a file).

The class `PluginBase` defines the available hooks and their signatures. To find out what hooks are available, what parameters they take and what output is expected, find the extensive documentation in `./yamp/plugins/base.py`, where all details are layed out.

Each plugin has to implement all of the hooks. However, by default most of the hook implementations return `None`, which indicates that they should be ignored.

### Third-Party Dependencies of Plugins

If a plugin has third-party dependencies, they can be installed in `./dependencies`.

For instance, when installing dependencies with `pip`, use the flag `--target=./dependencies` like so:

```
pip install requests --target=./dependencies
pip install -r some/requirements.txt --target=./dependencies
```

### Wrapping Connections

If more complex cryptographic protocols are used or if you have other very specific requirements, the decryption and encryption hooks might not be powerful enough to implement the desired functionality. This case arises, for instance, in TLS. To handle such situations, a plugin can wrap a connection.

By calling something like `my_connection.wrap()`, a plugin can take full and exclusive control over future read and write access to the specified stream(s). This way, the plugin has direct access to the underlying socket.

Note that wrappers will not be removed when a plugin is unloaded or reloaded, to keep the connection alive. This might be problematic if you wrap a single connection twice.

As a demonstration, see `./demo_plugins/ssl_termination_plugin.py`. For a more technical documentation, see `./yamp/proxy/connection.py`.


### Demo-Plugins

To familiarize yourself with plugins, some demonstrations can be found in the `./demo_plugins` folder.

**`my_awesome_plugin.py`** does some very basic filtering and logging for TCP connections. When a new TCP connection is built, we are notified by a logging message. If data is transmitted that contains the string `AAAAAAA`, the packet is dropped. If it contains the string `flag`, the packet is accepted. Otherwise, the filter ignores the packet. In the logging stage, we are notified about the data that is transmitted and about the action the filter has taken.

**`my_more_complex_plugin.py`** demonstrates how packages can be used as plugins. It simply prints out the data transmitted via TCP connections and additionally makes sends it to a request catcher.

TODO: `traffic_dump_wireguard.py`

## The Filter Engine

TODO
