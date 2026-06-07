# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: one-file native binary for Windows, macOS and Linux.

Bundles the web/PWA assets so the frozen app can serve its own UI offline.
Build with:  pyinstaller packaging/vpnfollower.spec
"""

import os

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("vpnfollower")  # ships vpnfollower/web/**

# Lets CI request a specific macOS slice, e.g. VPNF_TARGET_ARCH=universal2 to
# build a single binary that runs natively on both Intel and Apple Silicon.
target_arch = os.environ.get("VPNF_TARGET_ARCH") or None

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="vpnfollower",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)
