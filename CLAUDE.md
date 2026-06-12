# VPN-Follower

CLI + PWA that takes an IP / host / URL / self-connection and reports the
network, geolocation, RDAP/WHOIS, rDNS, and VPN/proxy/Tor/hosting signals behind
it, ending in a single verdict plus an evidence trail.

## Commands
- Run without installing: `python3 -m vpnfollower self`
- Install locally: `pip install .` then `vpnfollower <target>`
- Test: `pip install -e ".[test]"` then `pytest -q`
- Build desktop binary locally: `scripts/build_desktop.sh`

## Hard constraints
- **Standard library only at runtime.** Add NO third-party runtime dependencies
  (`dependencies = []` in pyproject.toml). pytest / pyinstaller / build are
  dev-only extras.
- Target **Python 3.9+**; do not use syntax newer than 3.9.
- Be honest about attribution limits — never imply the tool de-anonymizes a
  person behind a well-configured VPN. (See README, "What it can and cannot
  uncover.")

## Layout
- `vpnfollower/cli.py` — entry point (`vpnfollower` console script).
- `vpnfollower/orchestrator.py` — coordinates the lookups.
- `vpnfollower/sources/` — one module per data source (rdap, rdns, resolve,
  ipapi, dnsbl, tor, ports, vpn_heuristics). Add new signals here.
- `vpnfollower/report.py` / `models.py` — verdict + evidence formatting.
- `vpnfollower/server.py` + `vpnfollower/web/` — the PWA.
- `tests/` — pytest; add a test alongside any new source or heuristic.

## Conventions
- New data source = new module in `sources/`, wired into the orchestrator, with
  a matching `tests/test_*.py`.
- Keep network calls in `http.py`; respect existing timeout/error handling.
- Update the README usage section if you change CLI flags or output format.

## Releases (multi-platform)
The release pipeline already exists in `.github/workflows/release.yml`. One run
builds and publishes, in a single GitHub Release:

- **Windows** x64 native binary
- **macOS** universal2 binary (Intel + Apple Silicon)
- **Linux** x86_64 native binary
- **Python** wheel + sdist (runs anywhere Python does)
- **Web / ChromeOS / Android / iOS** — the installable **PWA** bundle
  (`vpnfollower-web-pwa.zip`). There are intentionally **no native `.ipa` /
  `.apk`** files: those mobile/ChromeOS targets are served by the PWA. Do not
  promise native mobile installers without a real native app project + signing.

How and when to cut a release:
- Trigger: after a **substantive** change has **merged to the main branch** and
  CI is green. Skip releases for docs-only/typo/formatting changes, and never
  release on every prompt.
- Bump the `version` in `pyproject.toml` (semver) in the same change set, then
  release by pushing a matching tag — `git tag vX.Y.Z && git push origin vX.Y.Z`
  — or by dispatching the **Release** workflow with that tag as input.
- The tag must match the bumped version (e.g. version `1.1.0` → tag `v1.1.0`).
- Refresh `packaging/RELEASE_NOTES.md` when the release is notable.

## Pull requests
- Develop on a feature branch and open a PR for review. **Do not merge without
  explicit approval**; do not enable auto-merge.
- After opening a PR, offer to watch it for CI + review comments.
