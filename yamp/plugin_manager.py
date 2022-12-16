import os
import logging
import traceback
import importlib

import pluggy

from .plugin_spec import PluginSpec
from .plugin import Plugin

hookspec = pluggy.HookspecMarker('yamp')


class PluginManager:

    def __init__(self):
        self._pm = pluggy.PluginManager('yamp')
        self._pm.add_hookspecs(PluginSpec)
        self._plugins = {}

    def reload(self):
        found_plugins = []
        with os.scandir("./plugins") as scanner:
            for candidate in scanner:
                if candidate.is_dir():
                    self.reload_plugin(candidate.name)
                    found_plugins += [candidate.name]
                elif candidate.is_file() and candidate.name.endswith(".py"):
                    self.reload_plugin(candidate.name[:-3])
                    found_plugins += [candidate.name[:-3]]
            else:
                # Ignore files not ending in .py and symlinks
                pass

        # unload all plugins that are not found
        # this copies the values into a temporary list to avoid modify-while-iterate
        for unload in [x for x in self._plugins.keys() if x not in found_plugins]:
            self.unload_plugin(unload)

    def reload_plugin(self, name):
        importlib.invalidate_caches()

        if name in self._plugins:
            # reload
            plugin = self._plugins[name]

            try:
                plugin.reload()
            except Exception as e:
                print(f"Error occurred while reloading plugin {name}")
                logging.error(traceback.format_exc())

        else:
            # fresh load
            try:
                plugin = Plugin(name, self._pm)
                plugin.load()
                self._plugins[name] = plugin
            except Exception as e:
                print(f"Error occurred while loading plugin {name}")
                logging.error(traceback.format_exc())

    def unload_plugin(self, name):
        # unload
        self._plugins[name].unload()
        del self._plugins[name]

    # --------- wrappers for hooks ------------

    def log(self, message):
        self._pm.hook.log(message=message)
