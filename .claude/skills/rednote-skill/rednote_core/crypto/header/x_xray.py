"""x-xray-traceid header generation — exact port of RedCrack header/X_Xray.py."""

from __future__ import annotations

import math
import random
import time


class _XrayState:
    """Mutable state for x-xray seq counter — mirrors XHS_Xray_Encrypt.__seq."""

    def __init__(self):
        self.seq = self._xb3_random(23)

    @staticmethod
    def _xb3_random(e: int) -> int:
        return math.floor(random.random() * math.pow(2, e))

    def get_seq(self) -> int:
        self.seq = self.seq + 1
        return self.seq

    def generate(self) -> str:
        """Generate x-xray-traceid — exact port of encrypt_headers_xray.

        Must be called BEFORE x-t timestamp is generated.
        Returns a 32-char hex string.
        """
        seq = self.get_seq()
        part1 = hex(int(time.time() * 1000) << 23 | seq)[2:].zfill(16)

        high32 = math.floor(random.random() * math.pow(2, 32))
        low32 = math.floor(random.random() * math.pow(2, 32))
        long_value = (high32 << 32) | low32
        part2 = hex(long_value)[2:].zfill(16)

        return part1 + part2


# Module-level singleton (one seq counter per process)
_xray = _XrayState()


def generate_x_xray_traceid() -> str:
    """Generate x-xray-traceid header value.

    Exact port of RedCrack XHS_Xray_Encrypt.encrypt_headers_xray.
    """
    return _xray.generate()
