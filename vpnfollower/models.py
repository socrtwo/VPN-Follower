"""Data structures shared across VPN-Follower."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Target:
    """The thing being investigated, after the raw input has been resolved."""

    raw: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    is_self: bool = False
    family: Optional[str] = None  # "IPv4" or "IPv6"
    error: Optional[str] = None


@dataclass
class Layer:
    """One layer of the investigation: the output of a single technique/source.

    Every source returns a Layer so that a failure in one source (e.g. the
    machine is offline) never aborts the whole investigation -- it just records
    ``ok=False`` with an error and the report carries on.
    """

    name: str
    ok: bool = True
    data: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ok": self.ok,
            "data": self.data,
            "notes": self.notes,
            "error": self.error,
        }


@dataclass
class Investigation:
    """The full result: the resolved target, every layer, and a verdict."""

    target: Target
    layers: list[Layer] = field(default_factory=list)
    verdict: dict = field(default_factory=dict)

    def add(self, layer: Layer) -> None:
        self.layers.append(layer)

    def layer(self, name: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def to_dict(self) -> dict:
        return {
            "target": asdict(self.target),
            "layers": [layer.to_dict() for layer in self.layers],
            "verdict": self.verdict,
        }
