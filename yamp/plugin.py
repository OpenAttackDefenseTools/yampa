from importlib import import_module, reload

from pluggy import PluginManager


class Plugin:
    def __init__(self, name, pm: PluginManager):
        self._module = import_module(f"plugins.{name}")
        self._impl = self._module.constructor()
        self._pm = pm

    def load(self):
        self._pm.register(self._impl)

    def unload(self):
        self._pm.unregister(self._impl)

    def reload(self):
        old_impl = self._impl
        reload(self._module)
        self._impl = self._module.constructor()
        new_impl = self._impl
        self._pm.unregister(old_impl)
        self._pm.register(new_impl)
