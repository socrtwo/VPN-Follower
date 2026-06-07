## VPN-Follower — install files

Pick the artifact for your platform. **ChromeOS, Android, iOS and Web** are all
served by the same installable web app (PWA); **Windows, macOS and Linux** also
have native one-file binaries; and `pip install` works on anything with Python.

| Platform | Artifact | How to install |
|---|---|---|
| **Windows** | `vpnfollower-windows-x64.zip` | Unzip, run `vpnfollower.exe`. Launches the app UI in your browser; or use it from a terminal as a CLI. |
| **macOS** | `vpnfollower-macos-universal2.tar.gz` | `tar xzf` and run `./vpnfollower`. One universal2 binary — runs natively on Intel **and** Apple Silicon. (Unsigned — first run: right-click → Open, or `xattr -dr com.apple.quarantine vpnfollower`.) |
| **Linux** | `vpnfollower-linux-*.tar.gz` | `tar xzf` and run `./vpnfollower`. |
| **ChromeOS** | `vpnfollower-web-pwa.zip` **or** the Linux binary | Use the PWA (below). ChromeOS can also run the Linux build under its Linux container. |
| **Android** | `vpnfollower-web-pwa.zip` (PWA) | Open the hosted app in Chrome → menu → **Install app / Add to Home screen**. |
| **iOS / iPadOS** | `vpnfollower-web-pwa.zip` (PWA) | Open the hosted app in Safari → Share → **Add to Home Screen**. |
| **Web** | `vpnfollower-web-pwa.zip` | Static files — host anywhere, or run `vpnfollower serve` and open the printed URL. |
| **Any (Python)** | `*.whl` / `*.tar.gz` | `pip install vpnfollower-*.whl` then `vpnfollower self`. |

### About the web / mobile build

The lookups (DNS, RDAP, sockets) cannot run inside a browser sandbox, so the
PWA talks to a small bundled backend. Start it with `vpnfollower serve` (or just
launch the native binary), then open/install the page. The PWA install **is**
the supported install path for Web, ChromeOS, Android and iOS.

> **Store-signed native mobile apps** (a Play Store `.aab` / App Store `.ipa`)
> require the maintainer's own Google Play and Apple Developer signing
> credentials, which can't live in CI. The PWA delivers the same functionality
> installable on those devices today; see `packaging/MOBILE.md` for the
> Briefcase-based path to signed store packages.

### Security & responsible use

Active port scanning is **off** by default everywhere and over the API requires
`--allow-scan`. Only scan hosts you are authorised to test. VPN-Follower reports
provider/registry-level attribution — not the real-world identity of a person.
