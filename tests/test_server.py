"""Integration tests for the web/API server (bound to an ephemeral port)."""

import json
import threading
import urllib.request

import pytest

from vpnfollower.server import _truthy, make_server


@pytest.fixture()
def server():
    httpd = make_server("127.0.0.1", 0, allow_scan=False)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        httpd.shutdown()
        httpd.server_close()


def _get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
        return r.status, r.headers, r.read()


def test_truthy():
    assert _truthy("1") and _truthy("true") and _truthy("YES")
    assert not _truthy("0") and not _truthy(None) and not _truthy("off")


def test_health(server):
    status, _, body = _get(server, "/api/health")
    assert status == 200
    data = json.loads(body)
    assert data["status"] == "ok"
    assert data["scan_enabled"] is False


def test_index_served(server):
    status, headers, body = _get(server, "/")
    assert status == 200
    assert "text/html" in headers.get("Content-Type", "")
    assert b"VPN" in body


def test_scan_blocked_without_flag(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(server, "/api/investigate?target=127.0.0.1&scan=1&rdap=0&tor=0&dnsbl=0")
    assert exc.value.code == 403


def test_path_traversal_blocked(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(server, "/../cli.py")
    assert exc.value.code == 404
