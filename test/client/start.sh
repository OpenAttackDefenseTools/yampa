#!/bin/bash
set -e
set -u

# Setup wireguard tunnel
ip link add yamp type wireguard
wg set yamp private-key <(echo "$NETWORK_PEER_PRIVATE") peer "$NETWORK_OWN_PUBLIC" endpoint yamp:51820 persistent-keepalive 1 allowed-ips 10.2.3.0/24
ip -4 address add 10.2.3.1/32 dev yamp
ip link set mtu 1420 up dev yamp
ip -4 route add 10.2.3.0/24 dev yamp

exec pytest /app/tests
