"""Offline tests for the VPN/proxy/hosting assessment logic."""

from vpnfollower.sources.vpn_heuristics import assess


def test_residential_is_minimal():
    layer = assess(
        {"isp": "Comcast Cable", "org": "Comcast", "as": "AS7922 Comcast",
         "asname": "COMCAST-7922", "proxy": False, "hosting": False},
        {},
    )
    assert layer.data["likelihood"] == "minimal"
    assert layer.data["score"] == 0


def test_known_vpn_provider_is_high():
    layer = assess(
        {"isp": "M247 Ltd", "org": "Mullvad VPN", "as": "AS9009 M247",
         "asname": "M247", "proxy": True, "hosting": True},
        {},
    )
    assert layer.data["likelihood"] == "high"
    assert any("VPN-provider keyword" in s for s in layer.data["signals"])


def test_datacenter_only_is_medium_or_low():
    layer = assess(
        {"isp": "DigitalOcean LLC", "org": "DigitalOcean",
         "as": "AS14061 DigitalOcean", "asname": "DIGITALOCEAN-ASN",
         "proxy": False, "hosting": True},
        {},
    )
    assert layer.data["likelihood"] in ("medium", "low")
    assert layer.data["score"] >= 2


def test_reverse_dns_datacenter_keyword_counts():
    layer = assess(
        {"isp": "Some ISP", "org": "", "as": "", "asname": "", "proxy": False},
        {"ptr": "vps-12345.hosting.example.net"},
    )
    assert layer.data["score"] >= 1
    assert any("reverse DNS" in s for s in layer.data["signals"])


def test_handles_empty_inputs():
    layer = assess(None, None)
    assert layer.ok is True
    assert layer.data["likelihood"] == "minimal"
