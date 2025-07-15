# -*- mode: python ; coding: utf-8 -*-

# Initially created by:
# pipenv run pyi-makespec --onefile --noconsole --add-data media\wr-icon.ico;media --icon media\wr-icon.ico --name wahoo-results --splash media\wr-card2.png --manifest wahoo-results.fileinfo wahoo_results.py

import os
import sys

block_cipher = None

# On Windows, we can set version information.
version_file = None
if sys.platform == "win32":
    version_file = "wahoo-results.fileinfo"

a = Analysis(
    ["wahoo_results.py"],
    pathex=[],
    binaries=[],
    datas=[(os.path.join("media", "wr-icon.ico"), "media")],
    hiddenimports=[
        # Needed starting with zeroconf 0.128.0 -> 0.131.0 transition
        "zeroconf._handlers.answers",
        "zeroconf._utils.ipaddress",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_datas = [
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
]

if sys.platform != "darwin":
    splash = Splash(
        #'media\\wr-card2.png',
        os.path.join("chromecast-receiver", "cc-receiver-logo.png"),
        binaries=a.binaries,
        datas=a.datas,
        text_pos=(10, 365),
        text_size=10,
        text_color="white",
        minify_script=True,
        always_on_top=True,
    )
    exe_datas.extend([splash, splash.binaries])

exe_datas.append([])

exe = EXE(
    *exe_datas,
    name="wahoo-results",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join("media", "wr-icon.ico"),
    version=version_file,
)
