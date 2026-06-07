"""Geolocation and network ownership via the free ip-api.com endpoint.

ip-api's free tier needs no API key and, when the relevant fields are
requested, returns ``proxy``, ``hosting`` and ``mobile`` flags that are useful
first-order signals for the VPN/proxy assessment. The free endpoint is HTTP
only and rate-limited to ~45 requests/minute.
"""

from __future__ import annotations

from ..http import get_json
from ..models import Layer

_FIELDS = ",".join(
    [
        "status", "message", "continent", "country", "countryCode", "region",
        "regionName", "city", "district", "zip", "lat", "lon", "timezone",
        "offset", "currency", "isp", "org", "as", "asname", "reverse",
        "mobile", "proxy", "hosting", "query",
    ]
)


def lookup(ip: str, timeout: float = 8.0) -> Layer:
    layer = Layer(name="Geolocation & network (ip-api)")
    try:
        data = get_json(f"http://ip-api.com/json/{ip}?fields={_FIELDS}", timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        layer.ok = False
        layer.error = str(exc)
        return layer

    if data.get("status") != "success":
        layer.ok = False
        layer.error = data.get("message", "lookup failed")
        return layer

    layer.data = data
    where = ", ".join(p for p in (data.get("city"), data.get("regionName"),
                                  data.get("country")) if p)
    if where:
        layer.notes.append(f"Located near {where} (provider-level accuracy only).")
    if data.get("proxy"):
        layer.notes.append("ip-api flags this address as a proxy / VPN / Tor node.")
    if data.get("hosting"):
        layer.notes.append("ip-api flags this address as a hosting / datacenter range.")
    return layer
