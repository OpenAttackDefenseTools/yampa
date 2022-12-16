import pluggy


def constructor():
    return MyAwesomePlugin()


hookimp = pluggy.HookimplMarker('yamp')

class MyAwesomePlugin:

    def __init__(self):
        self.prefix = "[*] "

    @hookimp
    def log(self, message):
        print(self.prefix + message)
