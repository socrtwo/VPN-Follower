"""Reverse DNS (PTR) lookup, with forward-confirmation.

A datacenter or VPN endpoint often gives itself away in its PTR record
(e.g. ``node-uk-london.mullvad.net`` or ``vps-1234.hosting.example``).
Forward-confirmation checks whether the PTR hostname resolves back to the same
IP -- unconfirmed PTRs are weaker evidence.
"""

from __future__ import annotations

import socket

from ..models import Layer


def lookup(ip: str, timeout: float = 5.0) -> Layer:
    layer = Layer(name="Reverse DNS (PTR)")
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        host, aliases, _ = socket.gethostbyaddr(ip)
    except Exception as exc:  # noqa: BLE001
        layer.ok = False
        layer.error = str(exc)
        return layer
    finally:
        socket.setdefaulttimeout(old)

    layer.data = {"ptr": host, "aliases": aliases}
    try:
        forward = {info[4][0] for info in socket.getaddrinfo(host, None)}
        layer.data["forward_confirmed"] = ip in forward
    except Exception:  # noqa: BLE001
        layer.data["forward_confirmed"] = None

    layer.notes.append(f"PTR record: {host}")
    if layer.data.get("forward_confirmed") is False:
        layer.notes.append("PTR is NOT forward-confirmed (weaker evidence).")
    return layer
