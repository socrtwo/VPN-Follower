"""WHOIS-style network registration data via RDAP.

rdap.org is a bootstrap that redirects to whichever Regional Internet Registry
(ARIN, RIPE, APNIC, ...) is authoritative for the address, so a single request
works worldwide with no API key. We surface the network block, the responsible
organisation, and the abuse contact -- the registry-level "owner" behind the
IP, which a VPN cannot hide.
"""

from __future__ import annotations

from ..http import get_json
from ..models import Layer


def _vcard_name(entity: dict) -> str | None:
    vcard = entity.get("vcardArray")
    if not isinstance(vcard, list) or len(vcard) < 2:
        return entity.get("handle")
    for field in vcard[1]:
        if isinstance(field, list) and field and field[0] == "fn":
            return field[-1]
    return entity.get("handle")


def _entity_email(entity: dict) -> str | None:
    vcard = entity.get("vcardArray")
    if not isinstance(vcard, list) or len(vcard) < 2:
        return None
    for field in vcard[1]:
        if isinstance(field, list) and field and field[0] == "email":
            return field[-1]
    return None


def lookup(ip: str, timeout: float = 10.0) -> Layer:
    layer = Layer(name="RDAP / WHOIS registration")
    try:
        data = get_json(f"https://rdap.org/ip/{ip}", timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        layer.ok = False
        layer.error = str(exc)
        return layer

    network = {
        "handle": data.get("handle"),
        "name": data.get("name"),
        "type": data.get("type"),
        "country": data.get("country"),
        "start_address": data.get("startAddress"),
        "end_address": data.get("endAddress"),
    }

    contacts = []
    for entity in data.get("entities", []) or []:
        contacts.append(
            {
                "roles": entity.get("roles", []),
                "name": _vcard_name(entity),
                "email": _entity_email(entity),
            }
        )

    layer.data = {
        "network": network,
        "contacts": contacts,
        "remarks": [
            line
            for remark in (data.get("remarks", []) or [])
            for line in (remark.get("description") or [])
        ],
    }
    if network.get("name"):
        layer.notes.append(f"Registered network: {network['name']} ({network.get('country') or '?'}).")
    abuse = [c for c in contacts if "abuse" in (c.get("roles") or [])]
    if abuse and abuse[0].get("email"):
        layer.notes.append(f"Abuse contact: {abuse[0]['email']}")
    return layer
