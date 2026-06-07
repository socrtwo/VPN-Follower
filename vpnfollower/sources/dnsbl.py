"""Check the address against public DNS blocklists (DNSBLs).

VPN, proxy and datacenter ranges are frequently listed on abuse/spam
blocklists. A listing is corroborating evidence that the address is shared,
hosted, or used to mask traffic. IPv4 only -- the classic DNSBL scheme reverses
the four octets under each blocklist zone.
"""

from __future__ import annotations

import socket

from ..models import Layer

_ZONES = {
    "zen.spamhaus.org": "Spamhaus ZEN",
    "bl.spamcop.net": "SpamCop",
    "b.barracudacentral.org": "Barracuda",
    "dnsbl.dronebl.org": "DroneBL",
    "all.s5h.net": "s5h",
}


def _reverse_octets(ip: str) -> str:
    return ".".join(reversed(ip.split(".")))


def lookup(ip: str, timeout: float = 4.0) -> Layer:
    layer = Layer(name="DNS blocklist (DNSBL) check")
    if ":" in ip:
        layer.ok = False
        layer.error = "DNSBL check supports IPv4 only"
        return layer

    rev = _reverse_octets(ip)
    listings: dict[str, str] = {}
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        for zone, name in _ZONES.items():
            try:
                result = socket.gethostbyname(f"{rev}.{zone}")
                listings[name] = result
            except socket.gaierror:
                pass  # not listed
            except Exception:  # noqa: BLE001
                pass  # transient resolver error -- skip this zone
    finally:
        socket.setdefaulttimeout(old)

    layer.data = {"listed_on": listings, "zones_checked": list(_ZONES.values())}
    if listings:
        layer.notes.append(f"Listed on {len(listings)} blocklist(s): {', '.join(listings)}.")
    return layer
