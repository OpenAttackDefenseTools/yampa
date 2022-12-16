import pluggy

hookimp = pluggy.HookimplMarker('yamp')

class HookImps:	
    
    def __init__(self):
        self.prefix = "[*] "
    
    @hookimp
    def log(self, message):
        print(self.prefix + message)
