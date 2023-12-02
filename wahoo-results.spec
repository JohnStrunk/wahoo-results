# -*- mode: python ; coding: utf-8 -*-

# Initially created by:
# pipenv run pyi-makespec --onefile --noconsole --add-data media\wr-icon.ico;media --icon media\wr-icon.ico --name wahoo-results --splash media\wr-card2.png --manifest wahoo-results.fileinfo wahoo_results.py

import inspect

# Figure out where ipinfo's data file is located
import os.path

block_cipher = None

a = Analysis(
    ["wahoo_results.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("media\\wr-icon.ico", "media"),
    ],
    hiddenimports=[],
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
splash = Splash(
    #'media\\wr-card2.png',
    "chromecast-receiver\\cc-receiver-logo.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(10, 365),
    text_size=10,
    text_color="white",
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    [],
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
    icon="media\\wr-icon.ico",
    version="wahoo-results.fileinfo",
)
