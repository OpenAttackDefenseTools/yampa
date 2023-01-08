import os
import ssl
import tempfile
from abc import ABC, abstractmethod
from functools import wraps

from yamp import *


def constructor():
    return TestSSLTerminationPlugin()


def wrap_ssl(function):
    @wraps(function)
    async def wrapper(self: "EncryptedStream", *args, **kwargs):
        if self._ssl is None:
            self._ssl = await self.create_ssl_object()

        while True:
            try:
                if not self._handshaked:
                    self._ssl.do_handshake()
                    self._handshaked = True

                ret = await function(self, *args, **kwargs)

                # Don't ask me why. Seriously. OpenSSL's docs say it raises a SSLWantRead/WriteError anytime a
                # blocking socket would block (which I assume is also during a normal write), but for some reason
                # we just don't seem to get the SSLWantWriteError. Instead, the outgoing BIO is just filled with
                # data and OpenSSL returns as if nothing happened.
                if self._outgoing.pending > 0:
                    await self.stream.write(self._outgoing.read())

                return ret
            except ssl.SSLWantReadError:
                if self._outgoing.pending > 0:
                    await self.stream.write(self._outgoing.read())

                data = await self.stream.read(4096)
                if len(data) == 0:
                    return b""
                self._incoming.write(data)
            except ssl.SSLWantWriteError:
                await self.stream.write(self._outgoing.read())

    return wrapper


class EncryptedStream(WrapperStream):
    def __init__(self):
        super().__init__()
        self._incoming = ssl.MemoryBIO()
        self._outgoing = ssl.MemoryBIO()
        self._ssl: ssl.SSLObject | None = None
        self._handshaked = False

    @abstractmethod
    async def create_ssl_object(self) -> ssl.SSLObject:
        pass

    @wrap_ssl
    async def do_read(self, n) -> bytes:
        return self._ssl.read(n)

    @wrap_ssl
    async def do_write(self, data: bytes):
        self._ssl.write(data)

    def do_close(self, force_close: bool):
        return self.stream.close(force_close)


class EncryptedServerStream(EncryptedStream):
    def __init__(self, cert: str, key: str):
        super().__init__()
        self._cert = cert
        self._key = key

    async def create_ssl_object(self) -> ssl.SSLObject:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        with tempfile.NamedTemporaryFile("w") as certfile:
            certfile.write(self._cert + "\n" + self._key)
            certfile.flush()
            context.load_cert_chain(certfile=certfile.name)

        return context.wrap_bio(self._incoming, self._outgoing, server_side=True)


class EncryptedClientStream(EncryptedStream):
    def __init__(self, cert: str):
        super().__init__()
        self._cert = cert

    async def create_ssl_object(self) -> ssl.SSLObject:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations(cadata=self._cert)
        return context.wrap_bio(self._incoming, self._outgoing, server_side=False)


class TestSSLTerminationPlugin(PluginBase):
    async def tcp_new_connection(self, connection: ProxyConnection) -> None:
        if connection.metadata.dst_port != 443:
            return None

        cert = os.environ["HTTPS_CERTIFICATE"]
        key = os.environ["HTTPS_KEY"]

        connection.wrap({ConnectionDirection.TO_SERVER: EncryptedClientStream(cert),
                         ConnectionDirection.TO_CLIENT: EncryptedServerStream(cert, key)})
