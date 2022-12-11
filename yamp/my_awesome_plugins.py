import pluggy

hookimp = pluggy.HookimplMarker('yamp')

class HookImps:	
    
    def __init__(self):
        self.prefix = "[yamp] "
    
    @hookimp
    def log(self, message):
        print(self.prefix + message)
