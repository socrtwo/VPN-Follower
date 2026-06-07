"""Offline tests for input resolution (no network needed for literals/URLs)."""

from vpnfollower.sources.resolve import _extract_host, resolve


def test_ipv4_literal():
    t = resolve("8.8.8.8")
    assert t.ip == "8.8.8.8"
    assert t.family == "IPv4"
    assert t.error is None


def test_ipv6_literal():
    t = resolve("2606:4700:4700::1111")
    assert t.family == "IPv6"
    assert t.ip == "2606:4700:4700::1111"


def test_extract_host_from_url():
    assert _extract_host("https://example.com/path?q=1") == "example.com"


def test_extract_host_strips_port_and_creds():
    assert _extract_host("user:pass@host.example:8080") == "host.example"


def test_extract_host_bracketed_ipv6_with_port():
    assert _extract_host("[2001:db8::1]:443") == "2001:db8::1"


def test_self_token_recognised():
    # We don't hit the network here; an empty token routes to the self branch
    # and (offline) returns an error rather than crashing.
    t = resolve("self")
    assert t.is_self is True
