from abc import ABC, abstractmethod

import mitmproxy_wireguard as wireguard


class ProxyStream(ABC):
    def __init__(self):
        self._interrupted = False
        self._read_buffer = b""
        self._closing = False

    @property
    def closing(self) -> bool:
        return self._closing

    @property
    def interrupted(self) -> bool:
        return self._interrupted

    def interrupt(self):
        self._interrupted = True

    def reset_interrupt(self):
        self._interrupted = False

    def _reset_buffer(self):
        x = self._read_buffer
        self._read_buffer = b""
        return x

    async def read(self, n) -> bytes:
        if self._interrupted:
            return b""

        if len(self._read_buffer) > 0:
            return self._reset_buffer()

        self._read_buffer = await self.do_read(n)

        if self._interrupted:
            return b""

        return self._reset_buffer()

    async def write(self, data: bytes):
        return await self.do_write(data)

    def close(self, force_close: bool = False):
        self.do_close(force_close or self._closing)
        self._closing = True

    @abstractmethod
    async def do_read(self, n) -> bytes:
        pass

    @abstractmethod
    async def do_write(self, data: bytes):
        pass

    @abstractmethod
    async def do_close(self, force_close: bool):
        pass


class WrapperStream(ProxyStream, ABC):
    def __init__(self):
        super().__init__()
        self._stream: ProxyStream | None = None

    @property
    def stream(self) -> ProxyStream:
        assert (self._stream is not None)
        return self._stream

    @stream.setter
    def stream(self, stream: ProxyStream):
        self._stream = stream

    def do_close(self, force_close: bool):
        if self._stream is not None:
            return self._stream.close(force_close)


class WireguardStream(ProxyStream):
    def __init__(self, stream: wireguard.TcpStream):
        super().__init__()
        self._stream = stream

    async def do_read(self, n) -> bytes:
        return await self._stream.read(n)

    async def do_write(self, data: bytes):
        self._stream.write(data)
        await self._stream.drain()

    def do_close(self, force_close: bool):
        if force_close:
            return self._stream.close()
        self._stream.write_eof()
