import aiohttp

from yamp import *


class MyPlugin(PluginBase):
    def __init__(self):
        self.prefix = "[!] "

    async def tcp_log(self, connection: ProxyConnection, metadata: Metadata, data: bytes,
                      action: None | tuple[FilterAction, bytes | None]) -> None:
        print(self.prefix, data)
        async with aiohttp.ClientSession() as session:
            await session.post("https://aaaaaasdf.requestcatcher.com/test", data=data.decode())
