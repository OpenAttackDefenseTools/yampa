import pluggy

hookspec = pluggy.HookspecMarker('yamp')


class PluginSpec:
    def decrypt(self, data):
        return data

    @hookspec(firstresult=True)
    def log(self, message):
        '''hook-specification for logging'''
