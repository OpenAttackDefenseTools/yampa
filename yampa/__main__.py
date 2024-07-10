import asyncio
import logging
import signal

from .proxy import Proxy


async def main():
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    proxy = Proxy()

    await proxy.start()

    async def close(*_):
        proxy.close()

    async def reload(*_):
        logging.info("Reloading plugins")
        await proxy.reload()

    asyncio.get_event_loop().add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(close()))
    asyncio.get_event_loop().add_signal_handler(signal.SIGUSR1, lambda: asyncio.ensure_future(reload()))

    await proxy.wait_closed()


asyncio.run(main())
