"""Offline tests for report rendering and the model containers."""

import json

from vpnfollower.models import Investigation, Layer, Target
from vpnfollower.report import to_json, to_text


def _sample() -> Investigation:
    inv = Investigation(target=Target(raw="1.1.1.1", ip="1.1.1.1", family="IPv4"))
    inv.add(Layer(name="Geolocation & network (ip-api)",
                  data={"city": "Sydney", "country": "Australia", "isp": "Cloudflare"},
                  notes=["Located near Sydney"]))
    inv.add(Layer(name="VPN / proxy / hosting assessment",
                  data={"score": 4, "likelihood": "medium", "signals": ["hosted"]}))
    inv.add(Layer(name="broken source", ok=False, error="offline"))
    inv.verdict = {"summary": "1.1.1.1 looks hosted.", "concealment_likelihood": "medium"}
    return inv


def test_to_json_roundtrips():
    inv = _sample()
    parsed = json.loads(to_json(inv))
    assert parsed["target"]["ip"] == "1.1.1.1"
    assert len(parsed["layers"]) == 3
    assert parsed["verdict"]["concealment_likelihood"] == "medium"


def test_to_text_contains_key_facts():
    text = to_text(_sample(), color=False)
    assert "VPN-FOLLOWER REPORT" in text
    assert "1.1.1.1" in text
    assert "medium" in text
    # failed layer is surfaced, not silently dropped
    assert "unavailable: offline" in text


def test_layer_lookup_helper():
    inv = _sample()
    assert inv.layer("broken source").error == "offline"
    assert inv.layer("does-not-exist") is None
