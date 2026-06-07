"""VPN-Follower: follow a connection through its layers of obfuscation.

VPN-Follower takes an IP address, hostname, URL, or your own live connection
and gathers every piece of intelligence that can be derived from it: the
network that owns the address, where it physically sits, its reverse DNS and
WHOIS records, whether it belongs to a known VPN / proxy / hosting provider or
a Tor exit node, and (optionally) which remote-access services it exposes.

It is an *attribution* tool, not a magic de-anonymiser. See README.md for an
honest description of what can and cannot be uncovered.
"""

__version__ = "1.0.0"
__all__ = ["investigate"]

from .orchestrator import investigate
