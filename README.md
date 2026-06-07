# VPN-Follower

**Follow a connection through its layers of obfuscation and report everything
that can be derived from it.**

Give VPN-Follower an IP address, hostname, URL, or your own live connection and
it peels back the layers an address hides behind — the network that owns it,
where it physically sits, its reverse DNS and registry (WHOIS) records, whether
it belongs to a known VPN / proxy / hosting provider or a Tor exit node, and
(optionally) which remote-access services it exposes. It then prints a single
**verdict** plus the full evidence trail.

```
$ vpnfollower 203.0.113.45

VERDICT
----------------------------------------------------------------
203.0.113.45 is high-likelihood VPN/proxy/hosting traffic on M247 Ltd near Amsterdam.
  concealment likelihood: high
  registered network: M247-NL
  - signal: Provider intelligence flags the address as proxy/VPN/Tor
  - signal: Known VPN-provider keyword in network identity: 'm247'
```

## What it can and cannot uncover (read this)

VPN-Follower is an **attribution** tool, not a magic de-anonymiser. Be honest
with yourself about what an IP can reveal:

- ✅ It *can* tell you the **network, provider, datacenter, registry owner, and
  abuse contact** behind an address — facts a VPN cannot hide, because the exit
  IP is still registered to *someone*.
- ✅ It *can* tell you, with good confidence, **whether** a connection is going
  through a VPN, proxy, hosting provider, or Tor — and how strongly the evidence
  points that way.
- ❌ It **cannot** reveal the **real-world identity of the person** using a
  well-configured VPN. That information lives only in the VPN operator's logs
  (if they keep any) and is obtainable only through a lawful legal process
  directed at that operator. No tool, including this one, conjures it from the
  packet.

In short: it follows the trail as far as public data goes, and tells you
exactly where the trail ends.

## Install

Pure Python standard library — **no dependencies required.**

```bash
git clone https://github.com/socrtwo/vpn-follower
cd vpn-follower
python3 -m vpnfollower self          # run without installing
# or install the console command:
pip install .
vpnfollower self
```

Requires Python 3.9+.

## Usage

```bash
vpnfollower self                  # investigate your own public address
vpnfollower 1.1.1.1               # a specific IP
vpnfollower https://example.com   # a URL or hostname (resolved first)
vpnfollower 8.8.8.8 --json        # machine-readable output
vpnfollower 203.0.113.10 --scan   # also actively probe common VPN ports
```

| Flag          | Effect                                              |
| ------------- | --------------------------------------------------- |
| `--json`      | Emit structured JSON instead of the text report     |
| `--scan`      | Actively probe common VPN/remote-access TCP ports   |
| `--no-rdap`   | Skip the RDAP/WHOIS registration lookup             |
| `--no-tor`    | Skip the Tor exit-node check                        |
| `--no-dnsbl`  | Skip the DNS blocklist check                        |
| `--timeout N` | Per-request network timeout in seconds (default 8)  |
| `--no-color`  | Disable coloured output                             |

### Web app (and the install target for mobile)

```bash
vpnfollower serve            # http://127.0.0.1:8721  -- open and "Install app"
vpnfollower serve --allow-scan   # also expose the active port-scan endpoint
```

`serve` launches an installable **Progressive Web App** plus a small JSON API
(`GET /api/investigate?target=…`). A browser can't perform raw DNS/RDAP/socket
lookups itself, so the page talks to this bundled backend. Binds to localhost by
default; `--host 0.0.0.0` exposes it (with a warning) and active scanning over
the API stays off unless `--allow-scan` is given.

## Install files / platforms

Every tagged [release](https://github.com/socrtwo/vpn-follower/releases) ships
ready-to-install artifacts, built automatically by CI:

| Platform | What to grab | Install |
|---|---|---|
| **Windows** | `vpnfollower-windows-x64.zip` | unzip → run `vpnfollower.exe` |
| **macOS** | `vpnfollower-macos-*.tar.gz` | `tar xzf` → `./vpnfollower` (Intel `x86_64` & Apple Silicon `arm64` builds) |
| **Linux** | `vpnfollower-linux-*.tar.gz` | `tar xzf` → `./vpnfollower` |
| **ChromeOS** | PWA, or the Linux binary | install the PWA, or run the Linux build in the Linux container |
| **Android** | the PWA | open in Chrome → **Install app** |
| **iOS / iPadOS** | the PWA | open in Safari → **Add to Home Screen** |
| **Web** | `vpnfollower-web-pwa.zip` | host the static files, or `vpnfollower serve` |
| **Any (Python)** | `*.whl` / `*.tar.gz` | `pip install vpnfollower-*.whl` |

The native desktop binaries are produced with PyInstaller; build one locally
with [`scripts/build_desktop.sh`](scripts/build_desktop.sh). Store-signed native
mobile packages (Play `.aab` / App Store `.ipa`) need the maintainer's own
signing credentials — see [`packaging/MOBILE.md`](packaging/MOBILE.md). The PWA
is the supported, signing-free install path for Web, ChromeOS, Android and iOS
today.

To cut a release: `git tag v1.2.3 && git push origin v1.2.3` — the
[release workflow](.github/workflows/release.yml) builds and publishes everything.

## How it works — the layers

Each "layer" is an independent source. If one fails (you're offline, a service
is rate-limiting), it's marked unavailable and the rest still run.

| Layer                       | Technique                                                            | What it reveals                                  |
| --------------------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| **Resolve**                 | Parse + DNS resolve the input                                       | The concrete IP behind a host/URL/`self`         |
| **Geolocation & network**   | [ip-api.com](https://ip-api.com) free endpoint (no key)             | City/country, ISP, ASN, proxy/hosting/mobile flags |
| **Reverse DNS (PTR)**       | `gethostbyaddr` + forward-confirmation                              | Datacenter/VPN naming in the PTR record          |
| **VPN/proxy assessment**    | Pure heuristics over the signals above                              | A scored likelihood + the signals that fired     |
| **RDAP / WHOIS**            | [rdap.org](https://rdap.org) bootstrap to the right RIR             | Registered network block, org, abuse contact     |
| **Tor exit-node check**     | Official Tor bulk exit list (cached 1h)                            | Definitive Tor-exit membership                   |
| **DNS blocklist (DNSBL)**   | Spamhaus / SpamCop / Barracuda / DroneBL / s5h                     | Abuse/shared-range reputation                    |
| **Active port probe**       | TCP connect to common VPN ports (`--scan`, opt-in)                 | Exposed OpenVPN/WireGuard/IPsec/PPTP/SoftEther   |

The scoring lives in
[`vpnfollower/sources/vpn_heuristics.py`](vpnfollower/sources/vpn_heuristics.py)
and is fully unit-tested offline.

## Responsible use

- **Active scanning (`--scan`) sends traffic to the target.** Only scan hosts
  you own or are explicitly authorised to test. Unauthorised scanning may be
  illegal in your jurisdiction.
- The passive lookups use only **publicly available** registry and provider
  data.
- Use this for legitimate purposes: fraud/abuse investigation, securing your
  own VPN, threat intelligence, network troubleshooting, and research.

## Development

```bash
pip install pytest
pytest          # 14 offline tests, no network required
```

## License

MIT © Paul D Pruitt — see [LICENSE](LICENSE).
