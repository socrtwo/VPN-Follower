"""Local HTTP/JSON API + static host for the VPN-Follower web app (PWA).

This turns the CLI engine into something the web, ChromeOS, Android and iOS
front-ends can talk to. A browser cannot perform raw DNS / RDAP / socket
operations itself, so the installable PWA calls this small backend.

Security: binds to 127.0.0.1 by default. Exposing it on a public interface
turns it into an open lookup proxy, so ``--host 0.0.0.0`` prints a warning and
the active port-scan endpoint stays disabled unless ``--allow-scan`` is passed.
Built on the standard library only.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .orchestrator import investigate

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _truthy(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


class _Handler(BaseHTTPRequestHandler):
    server_version = f"VPN-Follower/{__version__}"
    allow_scan = False  # set on the server instance via factory below

    # -- routing -----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        route = parsed.path
        if route == "/api/health":
            return self._json({"status": "ok", "version": __version__,
                               "scan_enabled": self.allow_scan})
        if route == "/api/investigate":
            return self._investigate(parse_qs(parsed.query))
        return self._static(route)

    # -- handlers ----------------------------------------------------------
    def _investigate(self, params: dict) -> None:
        target = (params.get("target", [""])[0] or "self").strip()
        want_scan = _truthy(params.get("scan", ["0"])[0])
        if want_scan and not self.allow_scan:
            return self._json(
                {"error": "active scanning is disabled on this server "
                          "(start with --allow-scan to enable)"},
                status=403,
            )
        try:
            inv = investigate(
                target,
                do_rdap=_truthy(params.get("rdap", ["1"])[0]),
                do_tor=_truthy(params.get("tor", ["1"])[0]),
                do_dnsbl=_truthy(params.get("dnsbl", ["1"])[0]),
                do_scan=want_scan,
            )
        except Exception as exc:  # noqa: BLE001 -- never 500 on a bad target
            return self._json({"error": str(exc)}, status=400)
        return self._json(inv.to_dict())

    def _static(self, route: str) -> None:
        rel = "index.html" if route in ("/", "") else route.lstrip("/")
        full = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not full.startswith(WEB_DIR) or not os.path.isfile(full):
            return self._json({"error": "not found"}, status=404)
        ext = os.path.splitext(full)[1].lower()
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", _CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- helpers -----------------------------------------------------------
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # quieter logging
        return


def make_server(host: str = "127.0.0.1", port: int = 8721,
                allow_scan: bool = False) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (_Handler,), {"allow_scan": allow_scan})
    return ThreadingHTTPServer((host, port), handler)


def serve(host: str = "127.0.0.1", port: int = 8721,
          allow_scan: bool = False) -> int:
    httpd = make_server(host, port, allow_scan)
    url = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}/"
    print(f"VPN-Follower web app serving at {url}")
    if host == "0.0.0.0":
        print("WARNING: bound to all interfaces -- this exposes a lookup proxy. "
              "Only do this on a trusted network.")
    print(f"Active scanning via API: {'ENABLED' if allow_scan else 'disabled'}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()
    return 0
