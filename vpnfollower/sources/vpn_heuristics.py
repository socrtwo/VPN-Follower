"""Combine signals into a VPN / proxy / hosting likelihood assessment.

This is pure logic (no network), which makes it the easiest part to unit-test.
It fuses the ip-api proxy/hosting flags with keyword matches against the
network identity (ISP / org / ASN name) and reverse DNS to produce a score and
a human-readable list of the signals that fired.
"""

from __future__ import annotations

from ..models import Layer

# Substrings strongly associated with consumer VPN providers / reseller ASNs.
VPN_KEYWORDS = [
    "vpn", "mullvad", "nordvpn", "nord vpn", "expressvpn", "express vpn",
    "protonvpn", "proton vpn", "private internet access", "cyberghost",
    "surfshark", "ipvanish", "windscribe", "tunnelbear", "perfect privacy",
    "azirevpn", "ovpn", "m247", "datacamp", "privado", "hide.me", "torguard",
    "purevpn", "mullvad", "boxpn", "vpnsecure", "frootvpn",
]

# Substrings that indicate a datacenter / cloud / hosting network (not a
# residential ISP). On their own these mean "hosted", which is necessary but
# not sufficient for "VPN".
HOSTING_KEYWORDS = [
    "hosting", "datacenter", "data center", "dedicated", "colo", "colocation",
    "cloud", "vps", "virtual server", "leaseweb", "ovh", "hetzner",
    "digitalocean", "linode", "vultr", "choopa", "quadranet", "psychz",
    "contabo", "scaleway", "g-core", "gcore", "amazon", "aws", "azure",
    "google cloud", "oracle cloud", "alibaba", "tencent", "server",
]


def _first_match(haystack: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        if kw in haystack:
            return kw
    return None


def assess(ipapi_data: dict | None, rdns_data: dict | None) -> Layer:
    layer = Layer(name="VPN / proxy / hosting assessment")
    ipapi_data = ipapi_data or {}
    rdns_data = rdns_data or {}

    identity = " ".join(
        str(ipapi_data.get(k, "")) for k in ("isp", "org", "as", "asname")
    ).lower()
    reverse = (ipapi_data.get("reverse") or rdns_data.get("ptr") or "").lower()

    signals: list[str] = []
    score = 0

    if ipapi_data.get("proxy"):
        signals.append("Provider intelligence flags the address as proxy/VPN/Tor")
        score += 4
    if ipapi_data.get("hosting"):
        signals.append("Address sits in a hosting/datacenter range, not a residential ISP")
        score += 2
    if ipapi_data.get("mobile"):
        signals.append("Mobile carrier network (CGNAT-shared, but not a commercial VPN)")

    vpn_kw = _first_match(identity, VPN_KEYWORDS) or _first_match(reverse, VPN_KEYWORDS)
    if vpn_kw:
        signals.append(f"Known VPN-provider keyword in network identity: '{vpn_kw}'")
        score += 4

    host_kw = _first_match(identity, HOSTING_KEYWORDS)
    if host_kw:
        signals.append(f"Datacenter/hosting keyword in network identity: '{host_kw}'")
        score += 2

    rev_host_kw = _first_match(reverse, HOSTING_KEYWORDS)
    if rev_host_kw:
        signals.append(f"Datacenter keyword in reverse DNS: '{rev_host_kw}'")
        score += 1

    if score >= 6:
        likelihood = "high"
    elif score >= 3:
        likelihood = "medium"
    elif score >= 1:
        likelihood = "low"
    else:
        likelihood = "minimal"

    layer.data = {
        "score": score,
        "likelihood": likelihood,
        "signals": signals,
        "network_identity": identity.strip(),
    }
    layer.notes.append(
        f"Concealment likelihood: {likelihood.upper()} (score {score})."
    )
    return layer
