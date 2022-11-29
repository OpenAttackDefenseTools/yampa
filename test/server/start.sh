#!/bin/bash
set -e
set -u

sleep 0.5

# Setup wireguard tunnel
ip link add yamp type wireguard
wg set yamp private-key <(echo "$PROXY_PEER_PRIVATE") listen-port 51820 peer "$PROXY_OWN_PUBLIC" endpoint yamp:51821 persistent-keepalive 1 allowed-ips 10.2.3.0/24
ip -4 address add 10.2.3.4/32 dev yamp
ip link set mtu 1420 up dev yamp
ip -4 route add 10.2.3.0/24 dev yamp

exec python3 -m app
