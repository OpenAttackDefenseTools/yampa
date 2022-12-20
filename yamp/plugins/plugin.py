import logging
import traceback
from importlib import import_module, reload

from .base import PluginBase

logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    def __init__(self, name):
        self._name = name
        self._module = None
        self._impl: PluginBase | None = None

    @property
    def name(self):
        return self._name

    def load(self):
        try:
            self._module = import_module(f"plugins.{self._name}")
            # Need to also reload in case a plugin was unloaded and loaded again
            reload(self._module)
            self._impl = self._module.constructor()
            return True
        except Exception as e:
            logger.error("Error occurred while reloading plugin %s", self._name)
            logger.error(traceback.format_exc())
            return False

    def unload(self):
        if self._impl is None:
            logging.warning("Unloaded a plugin before it was loaded: %s", self._name)
            return False

        return True

    def reload(self):
        if self._module is None:
            return self.load()

        try:
            reload(self._module)
            self._impl = self._module.constructor()
            return True
        except Exception as e:
            logger.error("Error occurred while reloading plugin %s", self._name)
            logger.error(traceback.format_exc())
            return False

    # Forward inherited methods to the Plugin impl
    def __getattribute__(self, name):
        if hasattr(PluginBase, name):
            if name in self._impl.__class__.__dict__:
                return getattr(self._impl, name)

        return object.__getattribute__(self, name)
