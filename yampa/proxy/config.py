import os
from dataclasses import dataclass

import mitmproxy_wireguard as wireguard


@dataclass
class WireguardConfig:
    own_private: str
    own_public: str
    peer_public: str
    peer_endpoint: str


@dataclass
class ProxyConfig:
    network: WireguardConfig
    proxy: WireguardConfig

    def __init__(self, e):
        network_own_private = e["NETWORK_OWN_PRIVATE"]
        network_own_public = e["NETWORK_OWN_PUBLIC"]
        network_peer_public = e["NETWORK_PEER_PUBLIC"]
        network_peer_endpoint = e.get("NETWORK_PEER_ENDPOINT", None)

        assert (network_own_public == wireguard.pubkey(network_own_private))

        self.network = WireguardConfig(network_own_private, network_own_public, network_peer_public,
                                       network_peer_endpoint)

        proxy_own_private = e["PROXY_OWN_PRIVATE"]
        proxy_own_public = e["PROXY_OWN_PUBLIC"]
        proxy_peer_public = e["PROXY_PEER_PUBLIC"]
        proxy_peer_endpoint = e.get("PROXY_PEER_ENDPOINT", None)

        assert (proxy_own_public == wireguard.pubkey(proxy_own_private))

        self.proxy = WireguardConfig(proxy_own_private, proxy_own_public, proxy_peer_public, proxy_peer_endpoint)


def load_config() -> ProxyConfig:
    return ProxyConfig(os.environ)
