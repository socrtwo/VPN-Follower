"""Drive every source and assemble the final Investigation + verdict."""

from __future__ import annotations

from .models import Investigation
from .sources import (
    dnsbl,
    ipapi,
    ports as ports_mod,
    rdap,
    rdns,
    resolve as resolve_mod,
    tor,
    vpn_heuristics,
)


def investigate(
    raw: str,
    *,
    do_rdap: bool = True,
    do_tor: bool = True,
    do_dnsbl: bool = True,
    do_scan: bool = False,
    timeout: float = 8.0,
) -> Investigation:
    """Run the full chase against ``raw`` (an IP, host, URL, or 'self')."""
    target = resolve_mod.resolve(raw)
    inv = Investigation(target=target)

    if not target.ip:
        inv.verdict = {"summary": target.error or "could not resolve target"}
        return inv

    ip = target.ip

    ipapi_layer = ipapi.lookup(ip, timeout=timeout)
    inv.add(ipapi_layer)

    rdns_layer = rdns.lookup(ip)
    inv.add(rdns_layer)

    assessment = vpn_heuristics.assess(
        ipapi_layer.data if ipapi_layer.ok else {},
        rdns_layer.data if rdns_layer.ok else {},
    )
    inv.add(assessment)

    if do_rdap:
        inv.add(rdap.lookup(ip, timeout=timeout))
    if do_tor:
        inv.add(tor.lookup(ip, timeout=max(timeout, 12.0)))
    if do_dnsbl and target.family == "IPv4":
        inv.add(dnsbl.lookup(ip))
    if do_scan:
        inv.add(ports_mod.scan(ip))

    inv.verdict = _summarize(inv)
    return inv


def _summarize(inv: Investigation) -> dict:
    verdict: dict = {}
    geo = inv.layer("Geolocation & network (ip-api)")
    assess = inv.layer("VPN / proxy / hosting assessment")
    tor_layer = inv.layer("Tor exit-node check")
    rdap_layer = inv.layer("RDAP / WHOIS registration")
    dnsbl_layer = inv.layer("DNS blocklist (DNSBL) check")

    if geo and geo.ok:
        verdict["location"] = ", ".join(
            p for p in (geo.data.get("city"), geo.data.get("regionName"),
                        geo.data.get("country")) if p
        ) or None
        verdict["network"] = geo.data.get("isp") or geo.data.get("org")
        verdict["asn"] = geo.data.get("as")

    if rdap_layer and rdap_layer.ok:
        verdict["registered_network"] = rdap_layer.data.get("network", {}).get("name")

    if assess:
        verdict["concealment_likelihood"] = assess.data.get("likelihood")
        verdict["signals"] = assess.data.get("signals", [])

    if tor_layer and tor_layer.ok and tor_layer.data.get("is_tor_exit"):
        verdict["tor_exit"] = True

    if dnsbl_layer and dnsbl_layer.ok and dnsbl_layer.data.get("listed_on"):
        verdict["blocklisted_on"] = list(dnsbl_layer.data["listed_on"])

    verdict["summary"] = _headline(inv, verdict)
    return verdict


def _headline(inv: Investigation, verdict: dict) -> str:
    ip = inv.target.ip
    likelihood = verdict.get("concealment_likelihood", "unknown")
    bits = [f"{ip}"]
    if verdict.get("tor_exit"):
        bits.append("is a Tor exit node")
    elif likelihood in ("high", "medium"):
        bits.append(f"is {likelihood}-likelihood VPN/proxy/hosting traffic")
    else:
        bits.append("looks like an ordinary endpoint (low concealment signal)")
    if verdict.get("network"):
        bits.append(f"on {verdict['network']}")
    if verdict.get("location"):
        bits.append(f"near {verdict['location']}")
    return " ".join(bits) + "."
