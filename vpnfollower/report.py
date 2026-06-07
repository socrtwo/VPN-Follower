"""Render an Investigation as JSON or as a human-readable text report."""

from __future__ import annotations

import json

from .models import Investigation

_RULE = "=" * 64
_THIN = "-" * 64


def to_json(inv: Investigation, indent: int = 2) -> str:
    return json.dumps(inv.to_dict(), indent=indent, default=str)


def to_text(inv: Investigation, color: bool = False) -> str:
    paint = _painter(color)
    lines: list[str] = [_RULE, paint("VPN-FOLLOWER REPORT", "bold"), _RULE]

    t = inv.target
    lines.append(f"Target input : {t.raw}")
    if t.hostname:
        lines.append(f"Hostname     : {t.hostname}")
    lines.append(f"Resolved IP  : {t.ip or '(unresolved)'}  [{t.family or '?'}]")
    if t.is_self:
        lines.append("Mode         : self (this machine's public address)")
    if t.error:
        lines.append(paint(f"Error        : {t.error}", "red"))

    # Verdict block first -- it's the takeaway.
    if inv.verdict:
        lines += ["", paint("VERDICT", "bold"), _THIN]
        summary = inv.verdict.get("summary")
        if summary:
            lines.append(paint(summary, "cyan"))
        for key in ("concealment_likelihood", "registered_network", "asn",
                    "tor_exit", "blocklisted_on"):
            if inv.verdict.get(key):
                lines.append(f"  {key.replace('_', ' ')}: {inv.verdict[key]}")
        for sig in inv.verdict.get("signals", []):
            lines.append(f"  - signal: {sig}")

    # Each layer in detail.
    for layer in inv.layers:
        lines += ["", paint(layer.name.upper(), "bold"), _THIN]
        if not layer.ok:
            lines.append(paint(f"  unavailable: {layer.error}", "yellow"))
            continue
        for note in layer.notes:
            lines.append(f"  * {note}")
        for key, value in _flatten(layer.data):
            lines.append(f"    {key}: {value}")

    lines += ["", _RULE,
              "Note: this is registry/provider-level attribution, not the real-world",
              "identity of a person. See README for what can and cannot be uncovered.",
              _RULE]
    return "\n".join(lines)


def _flatten(data: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out += _flatten(value, prefix=f"{path}.")
        elif isinstance(value, list):
            if not value:
                continue
            if all(not isinstance(v, (dict, list)) for v in value):
                out.append((path, ", ".join(str(v) for v in value)))
            else:
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        out += _flatten(item, prefix=f"{path}[{i}].")
                    else:
                        out.append((f"{path}[{i}]", str(item)))
        elif value not in (None, "", {}):
            out.append((path, str(value)))
    return out


_COLORS = {
    "bold": "\033[1m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
}
_RESET = "\033[0m"


def _painter(color: bool):
    def paint(text: str, style: str) -> str:
        if not color or style not in _COLORS:
            return text
        return f"{_COLORS[style]}{text}{_RESET}"

    return paint
