import asyncio
import os
import signal
import tempfile

import uvicorn


async def start_http():
    config = uvicorn.Config("app.http:app", host="0.0.0.0", port=80, log_level="info")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except asyncio.CancelledError as e:
        await server.shutdown()


async def start_https():
    certificate = os.environ["HTTPS_CERTIFICATE"]
    key = os.environ["HTTPS_KEY"]

    with tempfile.NamedTemporaryFile("w") as certfile, tempfile.NamedTemporaryFile("w") as keyfile:
        certfile.write(certificate)
        certfile.flush()
        keyfile.write(key)
        keyfile.flush()
        config = uvicorn.Config("app.http:app", host="0.0.0.0", port=443, log_level="info",
                                ssl_certfile=certfile.name, ssl_keyfile=keyfile.name)
        config.load()

    server = uvicorn.Server(config)
    try:
        await server.serve()
    except asyncio.CancelledError as e:
        await server.shutdown()


async def main():
    http_task = asyncio.create_task(start_http())
    https_task = asyncio.create_task(start_https())

    def stop():
        http_task.cancel()
        https_task.cancel()

    # delay signal handler registration until the servers are created
    # this is because only the last registered signal handler is called
    # and otherwise one uvicorn would break the other uvicorn graceful shutdown
    # pick a value that is long enough so the servers would start and short enough
    # that it happens before all tests passed. For now, 0.1s seems like a good idea
    await asyncio.sleep(0.1)
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stop)

    await asyncio.gather(http_task, https_task)


asyncio.run(main())
