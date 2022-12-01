import os
import re
import random
import string

from icmplib import ping


def test_ping_legitimate(hostname):
    for _ in range(10):
        while True:
            payload = os.urandom(56)

            # Regenerate if we match the flag
            if re.match(b"TESTFLAG_[A-Z]{20}", payload):
                continue
            break

        response = ping(hostname, count=1, timeout=0.1, payload=payload)

        assert response.is_alive


def test_ping_filtered(is_filtered, hostname):
    for _ in range(10):
        flag = f"TESTFLAG_{''.join(random.choice(string.ascii_uppercase) for _ in range(20))}".encode()
        payload = os.urandom(10) + flag + os.urandom(17)

        response = ping(hostname, count=1, timeout=0.1, payload=payload)

        assert response.is_alive != is_filtered
