"""A tiny, dependency-free HTTP helper built on urllib.

Kept deliberately small so VPN-Follower runs on a stock Python install with no
``pip install`` step. All network access flows through here so timeouts and the
User-Agent are applied consistently.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from . import __version__

USER_AGENT = f"VPN-Follower/{__version__} (+https://github.com/socrtwo/vpn-follower)"


def get(url: str, timeout: float = 8.0, headers: Optional[dict] = None) -> str:
    """Fetch a URL and return the decoded body, raising on any error."""
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted URLs)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def get_json(url: str, timeout: float = 8.0, headers: Optional[dict] = None) -> dict:
    """Fetch a URL and parse the body as JSON."""
    return json.loads(get(url, timeout=timeout, headers=headers))
