# Native mobile / store packages (Android `.aab`, iOS `.ipa`)

The published releases install on Android and iOS today via the **PWA** (open
the app in the browser → *Install app* / *Add to Home Screen*). That path needs
no signing credentials and is fully functional.

If you want **store-signed native packages**, use
[BeeWare Briefcase](https://briefcase.readthedocs.io/), which packages a Python
project for Android and iOS (as well as desktop and web) from one codebase. The
piece you must supply yourself is signing material — these are tied to your
identity and cannot be checked into the repo or generated in CI:

- **Android:** a Google Play upload keystore, and a Play Console account to
  distribute the `.aab`.
- **iOS:** an Apple Developer Program membership, a signing certificate and a
  provisioning profile (and a macOS machine with Xcode to build the `.ipa`).

## One-time setup

```bash
pip install briefcase
```

Add a `[tool.briefcase]` section to `pyproject.toml` pointing at a thin GUI
entry point (Briefcase apps need a GUI toolkit such as Toga; the existing
`vpnfollower.server` + web UI can be embedded in a WebView).

## Build

```bash
briefcase create android && briefcase build android   # -> .aab / .apk
briefcase create iOS     && briefcase build iOS        # -> .ipa  (macOS only)
```

Then sign with your own credentials and upload to the respective store. Once you
have a keystore/profile available to CI as encrypted secrets, the
`.github/workflows/release.yml` matrix can be extended with `android` / `ios`
jobs that attach these artifacts to the release automatically.
