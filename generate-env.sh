#!/bin/bash

set -e
set -u

if [ -f ".env" ]; then
	echo "Found .env, skipping generation"
	exit 0
fi

NETWORK_OWN_PRIVATE="$(wg genkey)"
NETWORK_OWN_PUBLIC="$(echo $NETWORK_OWN_PRIVATE | wg pubkey)"
NETWORK_PEER_PRIVATE="$(wg genkey)"
NETWORK_PEER_PUBLIC="$(echo $NETWORK_PEER_PRIVATE | wg pubkey)"

PROXY_OWN_PRIVATE="$(wg genkey)"
PROXY_OWN_PUBLIC="$(echo $PROXY_OWN_PRIVATE | wg pubkey)"
PROXY_PEER_PRIVATE="$(wg genkey)"
PROXY_PEER_PUBLIC="$(echo $PROXY_PEER_PRIVATE | wg pubkey)"


cat << EOF > .env
# To make sure logging output works
PYTHONUNBUFFERED=1

# For CTFs: fill in the gamenet config here
NETWORK_OWN_PRIVATE="$NETWORK_OWN_PRIVATE"
NETWORK_OWN_PUBLIC="$NETWORK_OWN_PUBLIC"
# peer private key is only used for testing
NETWORK_PEER_PRIVATE="$NETWORK_PEER_PRIVATE"
NETWORK_PEER_PUBLIC="$NETWORK_PEER_PUBLIC"

# For CTFs: fill in the connection to the vulnbox here
PROXY_OWN_PRIVATE="$PROXY_OWN_PRIVATE"
PROXY_OWN_PUBLIC="$PROXY_OWN_PUBLIC"
# peer private key is only used for testing
PROXY_PEER_PRIVATE="$PROXY_PEER_PRIVATE"
PROXY_PEER_PUBLIC="$PROXY_PEER_PUBLIC"

EOF

cat << EOF

.env generated. For local testing use e.g. following wireguard config

---------------------------------------------------------
[Interface]
PrivateKey = $NETWORK_PEER_PRIVATE
Address = 10.0.0.1/32
MTU = 1420

[Peer]
PublicKey = $NETWORK_OWN_PUBLIC
AllowedIPs = 10.0.0.0/24
Endpoint = 127.0.0.1:51820
PersistentKeepalive = 1
----------------------------------------------------------

and connect anywhere into the listed allowed ips

EOF
