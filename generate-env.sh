#!/bin/bash

set -e
set -u

# Generate .env
(
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

  cat <<EOF >.env
# To make sure logging output works
PYTHONUNBUFFERED=1

# For CTFs: fill in the gamenet config here
NETWORK_OWN_PRIVATE="$NETWORK_OWN_PRIVATE"
NETWORK_OWN_PUBLIC="$NETWORK_OWN_PUBLIC"
# peer private key is only used for testing
NETWORK_PEER_PRIVATE="$NETWORK_PEER_PRIVATE"
NETWORK_PEER_PUBLIC="$NETWORK_PEER_PUBLIC"
# Use this to start yamp without a fixed endpoint
#NETWORK_PEER_ENDPOINT="testclient:51820"

# For CTFs: fill in the connection to the vulnbox here
PROXY_OWN_PRIVATE="$PROXY_OWN_PRIVATE"
PROXY_OWN_PUBLIC="$PROXY_OWN_PUBLIC"
# peer private key is only used for testing
PROXY_PEER_PRIVATE="$PROXY_PEER_PRIVATE"
PROXY_PEER_PUBLIC="$PROXY_PEER_PUBLIC"
# Use this to start yamp without a fixed endpoint
#PROXY_PEER_ENDPOINT="testserver:51820"

EOF

  cat <<EOF

.env generated. For local testing use e.g. following wireguard config

---------------------------------------------------------
Network:
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
---------------------------------------------------------
Proxy:
---------------------------------------------------------
[Interface]
PrivateKey = $PROXY_PEER_PRIVATE
Address = 10.0.0.2/32
MTU = 1420

[Peer]
PublicKey = $PROXY_OWN_PUBLIC
AllowedIPs = 10.0.0.0/24
Endpoint = 127.0.0.1:51821
PersistentKeepalive = 1
---------------------------------------------------------

and connect anywhere into the listed allowed ips

EOF
)

# Generate .env-test

(
  set -e
  set -u

  if [ -f ".env-test" ]; then
    echo "Found .env-test, skipping generation"
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

  DIR="$(mktemp -d)"
  openssl req -x509 -newkey rsa:4096 -keyout "$DIR"/key.pem -out "$DIR"/cert.pem -nodes -subj '/CN=localhost' -addext "subjectAltName = DNS:testserver,IP:10.2.3.4" -sha256 -days 3650
  HTTPS_CERTIFICATE="$(cat "$DIR"/cert.pem)"
  HTTPS_KEY="$(cat "$DIR"/key.pem)"
  rm -rf "$DIR"

  cat <<EOF >.env-test
# To make sure logging output works
PYTHONUNBUFFERED=1

# For CTFs: fill in the gamenet config here
NETWORK_OWN_PRIVATE="$NETWORK_OWN_PRIVATE"
NETWORK_OWN_PUBLIC="$NETWORK_OWN_PUBLIC"
# peer private key is only used for testing
NETWORK_PEER_PRIVATE="$NETWORK_PEER_PRIVATE"
NETWORK_PEER_PUBLIC="$NETWORK_PEER_PUBLIC"
# Use this to start yamp without a fixed endpoint
NETWORK_PEER_ENDPOINT="testclient:51820"

# For CTFs: fill in the connection to the vulnbox here
PROXY_OWN_PRIVATE="$PROXY_OWN_PRIVATE"
PROXY_OWN_PUBLIC="$PROXY_OWN_PUBLIC"
# peer private key is only used for testing
PROXY_PEER_PRIVATE="$PROXY_PEER_PRIVATE"
PROXY_PEER_PUBLIC="$PROXY_PEER_PUBLIC"
# Use this to start yamp without a fixed endpoint
PROXY_PEER_ENDPOINT="testserver:51820"

HTTPS_CERTIFICATE="$HTTPS_CERTIFICATE"
HTTPS_KEY="$HTTPS_KEY"
EOF
)
