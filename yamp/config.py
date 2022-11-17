import os
from dataclasses import dataclass

import mitmproxy_wireguard as wireguard


@dataclass
class WireguardConfig:
    own_private: str
    own_public: str
    peer_public: str


@dataclass
class Config:
    network: WireguardConfig
    proxy: WireguardConfig

    def __init__(self, e):
        network_own_private = e["NETWORK_OWN_PRIVATE"]
        network_own_public = e["NETWORK_OWN_PUBLIC"]
        network_peer_public = e["NETWORK_PEER_PUBLIC"]

        assert (network_own_public == wireguard.pubkey(network_own_private))

        self.network = WireguardConfig(network_own_private, network_own_public, network_peer_public)

        proxy_own_private = e["PROXY_OWN_PRIVATE"]
        proxy_own_public = e["PROXY_OWN_PUBLIC"]
        proxy_peer_public = e["PROXY_PEER_PUBLIC"]

        assert (proxy_own_public == wireguard.pubkey(proxy_own_private))

        self.proxy = WireguardConfig(proxy_own_private, proxy_own_public, proxy_peer_public)


def load_config() -> Config:
    return Config(os.environ)
