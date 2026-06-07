"""Frozen-binary entry point used by PyInstaller.

When launched with no arguments (e.g. double-clicked as a desktop app) it opens
the installable web UI in the browser; otherwise it behaves exactly like the
``vpnfollower`` CLI.
"""

import sys
import threading
import webbrowser

from vpnfollower.cli import main
from vpnfollower.server import serve


def _gui() -> int:
    host, port = "127.0.0.1", 8721
    threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}/")).start()
    return serve(host=host, port=port)


if __name__ == "__main__":
    # No CLI args -> friendly app mode (launch the web UI). Any args -> CLI.
    raise SystemExit(_gui() if len(sys.argv) == 1 else main())
