import pluggy

hookspec = pluggy.HookspecMarker('yamp')

class HookSpecs:
	@hookspec
	def log(self, message):
		'''hook-specification for logging'''


class PM:
	
	def __init__(self):
		self.pm = pluggy.PluginManager('yamp')
		self.pm.add_hookspecs(HookSpecs)
	
	def load_plugins(self, module_name: str):
		try:
			module = __import__(module_name, fromlist=[''])
		except ImportError as e:
			print(f'Error: could not load module {module_name}:\n{e}')
			return
		
		self.pm.register(module.HookImps())
	
	def log(self, message):
		self.pm.hook.log(message=message)

