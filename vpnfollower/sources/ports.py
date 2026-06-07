"""Optional active TCP probe for VPN / remote-access services.

This is the only source that sends traffic *to the target*, so it is opt-in
(``--scan``). It performs a plain TCP connect on a short list of ports
associated with VPN endpoints. Many VPN protocols run over UDP (OpenVPN,
WireGuard, IKE/IPsec) and cannot be confirmed by a TCP connect, so an "open"
result is suggestive and a "closed" result is not conclusive.

Only ever scan hosts you are authorised to test.
"""

from __future__ import annotations

import socket

from ..models import Layer

# port -> (service description, transport note)
COMMON_PORTS = {
    443: "TLS (OpenVPN-over-TCP / AnyConnect / SoftEther / HTTPS-tunnel)",
    1194: "OpenVPN default (usually UDP)",
    1723: "PPTP",
    500: "IKE / IPsec (UDP)",
    4500: "IPsec NAT-T (UDP)",
    51820: "WireGuard (UDP)",
    1701: "L2TP (UDP)",
    992: "SoftEther / TELNETS",
    5555: "SoftEther alt",
    8443: "TLS-VPN admin / alt-HTTPS",
}


def scan(ip: str, timeout: float = 1.5, ports: list[int] | None = None) -> Layer:
    layer = Layer(name="Active port probe (VPN/remote-access services)")
    layer.notes.append(
        "Active probe -- only run against targets you are authorised to test."
    )

    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    results: dict[int, dict] = {}
    for port in (ports or sorted(COMMON_PORTS)):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                state = "open" if sock.connect_ex((ip, port)) == 0 else "closed/filtered"
        except Exception as exc:  # noqa: BLE001
            state = f"error: {exc}"
        results[port] = {"service": COMMON_PORTS.get(port, "unknown"), "state": state}

    open_ports = [p for p, v in results.items() if v["state"] == "open"]
    layer.data = {"ports": results, "open_ports": open_ports}
    if open_ports:
        layer.notes.append(
            "Open TCP ports consistent with VPN/remote-access: "
            + ", ".join(str(p) for p in open_ports)
        )
    return layer
