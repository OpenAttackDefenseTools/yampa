import pluggy

hookspec = pluggy.HookspecMarker('yamp')

class HookSpecs:
	@hookspec
	def log(self, message):


class PM:
	
	def __init__(self):
		self._pm = pluggy.PluginManager('yamp')
		self._pm.add_hookspecs(HookSpecs)
	
	def load_plugins(self, module_name: str):
		try:
			module = __import__(module_name, fromlist=[''])
		except ImportError as e:
			print(f'Error: could not load module {module_name}:\n{e}')
			return
		
		self._pm.register(module.HookImps())
	
	def unregister_plugins(self):
		self._pm.unregister()
	
	# --------- wrappers for hooks ------------
	
	def log(self, message):
		self._pm.hook.log(message=message)

