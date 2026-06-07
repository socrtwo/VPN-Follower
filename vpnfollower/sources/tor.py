"""Check whether an address is a published Tor exit node.

Downloads the official Tor Project bulk exit list and caches it for an hour so
repeated investigations don't re-fetch it. Membership is definitive evidence
that traffic from the address is Tor exit traffic.
"""

from __future__ import annotations

import os
import tempfile
import time

from ..http import get
from ..models import Layer

_EXIT_LIST_URL = "https://check.torproject.org/torbulkexitlist"
_CACHE_PATH = os.path.join(tempfile.gettempdir(), "vpnfollower_tor_exits.txt")
_CACHE_TTL = 3600  # seconds


def _load_exit_ips(timeout: float) -> set[str]:
    if os.path.exists(_CACHE_PATH) and (time.time() - os.path.getmtime(_CACHE_PATH)) < _CACHE_TTL:
        with open(_CACHE_PATH, encoding="utf-8") as fh:
            return {line.strip() for line in fh if line.strip()}

    text = get(_EXIT_LIST_URL, timeout=timeout)
    ips = {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    }
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as fh:
            fh.write("\n".join(sorted(ips)))
    except OSError:
        pass  # cache is best-effort
    return ips


def lookup(ip: str, timeout: float = 12.0) -> Layer:
    layer = Layer(name="Tor exit-node check")
    try:
        exits = _load_exit_ips(timeout)
    except Exception as exc:  # noqa: BLE001
        layer.ok = False
        layer.error = str(exc)
        return layer

    is_exit = ip in exits
    layer.data = {"is_tor_exit": is_exit, "exit_list_size": len(exits)}
    if is_exit:
        layer.notes.append("This IP is a known Tor exit node -- traffic is anonymised via Tor.")
    return layer
