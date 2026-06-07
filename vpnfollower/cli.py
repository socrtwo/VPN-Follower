"""Command-line interface for VPN-Follower.

Two modes:
  * ``vpnfollower <target> [flags]``  -- investigate and print a report (default)
  * ``vpnfollower serve [flags]``     -- run the web app (PWA) + JSON API
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .orchestrator import investigate
from .report import to_json, to_text

_EPILOG = """\
examples:
  vpnfollower self                 # investigate your own public address
  vpnfollower 1.1.1.1              # a specific IP
  vpnfollower https://example.com  # resolve a URL/host first
  vpnfollower 203.0.113.10 --scan  # include an active VPN-port probe
  vpnfollower 8.8.8.8 --json       # machine-readable output
  vpnfollower serve                # launch the installable web app (PWA)

Attribution only. VPN-Follower reports the network/registry/provider behind an
address; it does not reveal the real-world identity of a person. Only actively
scan (--scan) hosts you are authorised to test.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vpnfollower",
        description="Follow a connection through its layers of obfuscation and "
                    "report everything that can be derived from it.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target", nargs="?", default="self",
        help="IP, hostname, URL, or 'self' (default: self)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--scan", action="store_true",
                        help="actively probe common VPN ports (authorised targets only)")
    parser.add_argument("--no-rdap", action="store_true", help="skip RDAP/WHOIS lookup")
    parser.add_argument("--no-tor", action="store_true", help="skip Tor exit-node check")
    parser.add_argument("--no-dnsbl", action="store_true", help="skip DNS blocklist check")
    parser.add_argument("--timeout", type=float, default=8.0,
                        help="per-request network timeout in seconds (default: 8)")
    parser.add_argument("--no-color", action="store_true", help="disable coloured output")
    parser.add_argument("--version", action="version", version=f"VPN-Follower {__version__}")
    return parser


def build_serve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vpnfollower serve",
        description="Run the VPN-Follower web app (installable PWA) and JSON API.",
    )
    parser.add_argument("--host", default="127.0.0.1",
                        help="interface to bind (default: 127.0.0.1; use 0.0.0.0 to expose)")
    parser.add_argument("--port", type=int, default=8721, help="port (default: 8721)")
    parser.add_argument("--allow-scan", action="store_true",
                        help="permit the active port-scan endpoint over the API")
    return parser


def _run_investigate(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    inv = investigate(
        args.target,
        do_rdap=not args.no_rdap,
        do_tor=not args.no_tor,
        do_dnsbl=not args.no_dnsbl,
        do_scan=args.scan,
        timeout=args.timeout,
    )
    if args.json:
        print(to_json(inv))
    else:
        color = (not args.no_color) and sys.stdout.isatty()
        print(to_text(inv, color=color))
    return 0 if inv.target.ip else 1


def _run_serve(argv: list[str]) -> int:
    from .server import serve  # imported lazily so investigate mode stays light

    args = build_serve_parser().parse_args(argv)
    return serve(host=args.host, port=args.port, allow_scan=args.allow_scan)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "serve":
        return _run_serve(argv[1:])
    return _run_investigate(argv)


if __name__ == "__main__":
    raise SystemExit(main())
