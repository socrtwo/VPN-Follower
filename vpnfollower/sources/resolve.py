"""Turn whatever the user typed into a concrete IP address.

Accepts: a bare IPv4/IPv6 literal, a hostname, a full URL, a ``user@host``
form, ``host:port``, or one of the "self" tokens to investigate the machine's
own public address.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from ..http import get
from ..models import Target

SELF_TOKENS = {"", "self", "me", "myip", "mine", "."}

# Providers that simply echo back the caller's public IP, tried in order.
_PUBLIC_IP_URLS = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
)


def _public_ip() -> str | None:
    for url in _PUBLIC_IP_URLS:
        try:
            ip = get(url, timeout=6).strip()
            ipaddress.ip_address(ip)  # validate
            return ip
        except Exception:
            continue
    return None


def _extract_host(token: str) -> str:
    """Strip scheme, path, credentials and port to leave a bare host."""
    host = token
    if "://" in host:
        host = urlparse(host).hostname or host
    else:
        # No scheme: chop any path, then treat the rest as authority.
        host = host.split("/", 1)[0]
        if "@" in host:
            host = host.rsplit("@", 1)[-1]
        host = _strip_port(host)
    return host.strip().strip("[]")


def _strip_port(host: str) -> str:
    host = host.strip()
    if host.startswith("["):  # bracketed IPv6, optionally with :port
        return host[1: host.index("]")] if "]" in host else host
    if host.count(":") == 1:  # host:port or ipv4:port (IPv6 has many colons)
        return host.split(":", 1)[0]
    return host


def resolve(raw: str) -> Target:
    token = (raw or "").strip()

    if token.lower() in SELF_TOKENS:
        ip = _public_ip()
        if not ip:
            return Target(raw=raw or "self", is_self=True,
                          error="could not determine this machine's public IP")
        return Target(raw=raw or "self", ip=ip, is_self=True,
                      family="IPv6" if ":" in ip else "IPv4")

    host = _extract_host(token)

    # Already an IP literal?
    try:
        ipobj = ipaddress.ip_address(host)
        return Target(raw=raw, ip=str(ipobj),
                      family="IPv6" if ipobj.version == 6 else "IPv4")
    except ValueError:
        pass

    # Otherwise resolve the hostname.
    try:
        infos = socket.getaddrinfo(host, None)
        ip = infos[0][4][0]
        return Target(raw=raw, ip=ip, hostname=host,
                      family="IPv6" if ":" in ip else "IPv4")
    except Exception as exc:  # noqa: BLE001
        return Target(raw=raw, hostname=host,
                      error=f"could not resolve '{host}': {exc}")
