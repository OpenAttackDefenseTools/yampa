# YAMP -- User Manual

## Overview

YAMP is Yet Another Mitm Proxy for use in A/D CTFs.
It is intended to sit in between the gamenet and vulnbox and can be customized via plugins to perform different functionality on the traffic.

Fun fact: Yamp is also the short name for [various plants native to western North America](https://en.wikipedia.org/wiki/Perideridia).

## Setup

Since YAMP runs in docker, you hardly have to take care of prerequisites -- except for docker, of course.

Note that a fairly recent version of both docker and the docker compose plugin is required.

To set up YAMP, do the following:

1. Clone the repository.
(In the rest of the documentantion, `./` refers to the repository.)
2. Generate a sample environment using `./generate-env.sh`
3. Edit `.env` and adjust the config as you need

At this point, YAMP should be ready to run.
To start it, use the following command:

```bash
docker compose up -d
```

## Plugins

When YAMP is started up freshly without any plugins*, the proxy will behave transparently.
That is, it will forward traffic in both directions without modifying, filtering or logging it.
To do so, you will want to add plugins.

A plugin implements multiple hooks.
The hooks have the following intended functionality:

* decrypting
* filtering
* logging
* encrypting

You can think of a data packet as walking through these stages in the above order.

When multiple plugins are loaded, the respective hooks of all plugins are executed one after the other with the same input parameters.
When a hook returns `None`, the hook of the next plugin in sequence will be called.
If a hook returns something different from `None` (for instance, when the decryption hook returns decrypted data), the rest of the chain is dropped and this output will be taken as the output of the chain.
This means that by returning `None`, a hook can indicate that a certain data packet is `None` of its business and that the next plugin (if any) should take care of it.

Exception to this are such hooks that don't have a return value, like logging, `tcp_new_connection` and `tcp_connection_close`.
For these hooks, the respective implementations of all loaded plugins are executed in parallel.

Find more details on the implementation of plugins in the section "Writing Plugins".

Note * `filter_plugin.py` is always installed and active.
However, without adding meaningful rules into `./rules/`, it will not filter anything.

### Loading Plugins

To add your plugins, add them to your specified plugin directory (e.g. `./plugins`).
For the changes to take effect during runtime, call `./reload.sh`.
YAMP will then unload all plugins, reload the code and initialize them again.

If an old version of a plugin is running and an error arises while loading the newer version, the old version will keep running.
That is, plugins are only replaced if at least the load process is successful.

### Writing Plugins

On a technical level, a plugin is a python module (or package) that exposes a function of the following signature:

```python
def constructor() -> PluginBase: ...
```

That is, the constructor returns an instance of a *direct* subclass of `PluginBase`.
You can use the constructor to do some initialization (like loading filter rules from a file).

The class `PluginBase` defines the available hooks and their signatures.
To find out what hooks are available, what parameters they take and what output is expected, find the extensive documentation in `./yamp/plugins/base.py`, where all details are layed out.

You can implement a hook by simply overriding the base function.
Since PluginBase only specifies a default for when no plugin overrides a given hook, there is no need to call super().

### Third-Party Dependencies of Plugins

If a plugin has third-party dependencies, they can be installed in `./dependencies`.

For instance, when installing dependencies with `pip`, use the flag `--target=./dependencies` like so:

```bash
pip install requests --target=./dependencies
pip install -r some/requirements.txt --target=./dependencies
```

Since `./dependencies` is mounted into the docker container, you can install dependencies at runtime and issue a `./reload.sh` afterwards.

### Wrapping Connections

If more complex cryptographic protocols are used or if you have other very specific requirements, the decryption and encryption hooks might not be powerful enough to implement the desired functionality.
This case arises, for instance, in TLS.
To handle such situations, a plugin can wrap a connection.

By calling something like `my_connection.wrap()`, a plugin can take full and exclusive control over future read and write access to the specified stream(s).
This way, the plugin has direct access to the underlying socket.

Note that wrappers will not be removed when a plugin is unloaded or reloaded, to keep the connection alive.
This might be problematic if you wrap a single connection twice.

As a demonstration, see `./demo_plugins/ssl_termination_plugin.py`.
For a more technical documentation, see `./yamp/proxy/connection.py`.


### Demo-Plugins

To familiarize yourself with plugins, some demonstrations can be found in the `./demo_plugins` folder.

- **`my_awesome_plugin.py`** does some very basic filtering and logging for TCP connections.
When a new TCP connection is built, we are notified by a logging message.
If data is transmitted that contains the string `AAAAAAA`, the connection is closed.
If it contains the string `flag`, the packet is accepted.
Otherwise, the filter ignores the packet.
In the logging stage, we are notified about the data that is transmitted and about the action the filter has taken.
- **`my_more_complex_plugin.py`** demonstrates how packages can be used as plugins.
It simply prints out the data transmitted via TCP connections and additionally makes sends it to a request catcher.
- **`traffic_dump_wireguard.py`** starts a third wireguard endpoint on port 51822 and creates a live replay of traffic passing through the proxy.
You can use this (after tweaking the config) to extract live traffic captures from the "middle" of the proxy chain, i.e.
the log stage.
- **`ssl_termination_plugin`** reads a tls certificate and key from the environment and intercepts any connections targeting port 443 on the inside of the proxy.
It uses the connection wrapping API to transparently decrypt and re-encrypt TLS.
You can re-use this plugin by simply swapping out the key, cert and port used.

## The Filter Engine

The current (very limited) filter engine is implemented in rust and used in python using pyo3 bindings and the maturin build system.

Upon plugin (re)load, all `rules/*.rls` files are read and concatenated (files are concatenated in alphabetic order).

To avoid syntax errors at runtime (which only cause needless overhead), you can run `./lint-rules.sh` to quickly check the rules directory.
In case of syntax errors, the linter will print out all faulty lines and exit with code 1.
If there is no error parsing the rules, the linter will output nothing and exit with code 0.

This allows for simple combination of the linter with the reload script like so:
```bash
 ./lint-rules.sh && ./reload.sh
```

Furthermore, the filter plugin will automatically generate a log similar to suricata's [eve.json](https://github.com/OISF/suricata/blob/master/doc/userguide/output/eve/eve-json-format.rst).
This log will be placed under `./rules/eve.json`.

### Rules
The rule format is as follows:

> RULE ::= EFFECTS `:` DIRECTION `:` MATCHERS `;`
> 
> EFFECTS ::= (ACTION | TAGS | FLOWS)
> 
> ACTION ::= (`ACCEPT` | `ALERT` | `DROP`)[`(`(QUOTED_STRING)`)`]
> 
> TAGS ::= `TAGS(`{QUOTED_STRING}+`)`
> 
> FLOWS ::= `FLOWS(`{QUOTED_STRING}+`)`
> 
> DIRECTION ::= (`IN` | `OUT`)[`(`U16 [`,` U16] `)`]
> 
> MATCHERS ::= (REGEX | FLOW)
> 
> REGEX ::= QUOTED_STRING
> 
> FLOW ::= `SET(`QUOTED_STRING`)`

One rule might look like this:

`DROP("contains flag") TAG("whatever") : OUT(8080) : "FLAG\{";`

Here, a packet where the ascii bytes of `FLAG{` would be contained with the message "contains flag" and emits the tag "whatever"

### Direction

This part is optimized for what we think is the most likely needed on a regular basis:
You can specify the direction as incoming or outgoing and then either no port (all ports match), one port, which is the port on the vulnbox side or two ports.
In this case the first is the port on the vulnbox side and the second one is the other port.
The case where only one port is specified will usually be the most required.

### Flow bits

Flow bits are currently quite limited.
They are managed per connection by the python plugin, one can add flow bits as an effect of the rule and match them in the matcher part.

### Extendability

The parser for the rules is written in `nom`, a powerful combination parser.
It is therefore quite easy to add capability to the rules.
