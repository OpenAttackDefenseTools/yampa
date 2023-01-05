import asyncio
import logging
import os
import importlib
import traceback
import typing

from .base import PluginBase
from .plugin import Plugin

logger = logging.getLogger(__name__)


class PluginManager(PluginBase):
    def __init__(self):
        self._default_plugin = PluginBase()
        self._plugins = {}
        self._open_connections = set()

    async def reload(self):
        success = True

        found_plugins = []
        with os.scandir("./plugins") as scanner:
            for candidate in scanner:
                if candidate.name.startswith("."):
                    # Ignore
                    pass
                elif candidate.is_dir():
                    if not os.path.isfile(os.path.join(candidate.path, "__init__.py")):
                        logger.info("... skipping directory %s: does not have __init__.py", candidate)
                        continue
                    success &= await self.reload_plugin(candidate.name)
                    found_plugins += [candidate.name]
                elif candidate.is_file() and candidate.name.endswith(".py"):
                    success &= await self.reload_plugin(candidate.name[:-3])
                    found_plugins += [candidate.name[:-3]]
                else:
                    # Ignore files not ending in .py and symlinks
                    pass

        # unload all plugins that are not found
        # this copies the values into a temporary list to avoid modify-while-iterate
        for unload in [x for x in self._plugins.keys() if x not in found_plugins]:
            success &= self.unload_plugin(unload)

        return success

    async def reload_plugin(self, name):
        importlib.invalidate_caches()

        if name in self._plugins:
            # reload
            logger.info("... reloading %s", name)
            plugin = self._plugins[name]

            success = plugin.reload()
        else:
            # fresh load
            logger.info("... fresh loading %s", name)
            plugin = Plugin(name)
            success = plugin.load()
            self._plugins[name] = plugin

        # replay all open connection closed
        await asyncio.gather(*[plugin.tcp_new_connection(conn) for conn in self._open_connections])
        return success

    def unload_plugin(self, name):
        # unload
        logger.info("... unloading %s", name)
        success = self._plugins[name].unload()
        del self._plugins[name]
        return success

    def __getattribute__(self, name):
        if hasattr(PluginBase, name):
            # store history for open TCP connections
            if name == "tcp_new_connection":
                async def wrapper(connection, *args, **kwargs):
                    self._open_connections.add(connection)
                    await self._delegate_plugin_call(name)(connection, *args, **kwargs)
            elif name == "tcp_connection_closed":
                async def wrapper(connection, *args, **kwargs):
                    self._open_connections.remove(connection)
                    await self._delegate_plugin_call(name)(connection, *args, **kwargs)

            else:
                return self._delegate_plugin_call(name)
            return wrapper

        return object.__getattribute__(self, name)

    # Forward plugin calls to all plugins
    def _delegate_plugin_call(self, name):
        spec = getattr(PluginBase, name)

        logger.debug("Executing plugin hook %s", name)

        async def catchall(plugin, awaitable):
            try:
                return await awaitable
            except Exception as e:
                logger.error("Error occurred while executing plugin %s, skipping and unloading...", plugin.name)
                logger.error(traceback.format_exc())
                self.unload_plugin(plugin.name)
                return None

        if typing.get_type_hints(spec)["return"] is type(None):
            # If the function is annotated to never return anything other than None, execute all plugins
            async def _my_plugin_forwarder(*args, **kwargs):
                await asyncio.gather(*[catchall(plugin, getattr(plugin, name)(*args, **kwargs))
                                       for plugin in self._plugins.values() if hasattr(plugin, name)])
        else:
            # Otherwise, run them until the first not-None result appears
            async def _my_plugin_forwarder(*args, **kwargs):
                for plugin in [x for x in self._plugins.values() if hasattr(x, name)]:
                    if (ret := await catchall(plugin, getattr(plugin, name)(*args, **kwargs))) is not None:
                        return ret
                # If no plugin is implemented or all plugins return None, run a default implementation
                return await getattr(self._default_plugin, name)(*args, **kwargs)

        return _my_plugin_forwarder
