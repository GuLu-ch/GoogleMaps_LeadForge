# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


qfluentwidgets_datas = collect_data_files("qfluentwidgets")
qfluentwidgets_hiddenimports = collect_submodules("qfluentwidgets")


a = Analysis(
    ["src/gmap_collector/main.py"],
    pathex=["src", "."],
    binaries=[],
    datas=qfluentwidgets_datas,
    hiddenimports=[
        "scripts.cleanup_runtime_data",
        *qfluentwidgets_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GoogleMaps_LeadForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GoogleMaps_LeadForge",
)
