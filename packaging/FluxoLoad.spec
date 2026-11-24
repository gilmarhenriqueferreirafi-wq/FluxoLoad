# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.datastruct import Tree


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        (r'C:\Program Files\nodejs\node.exe', 'third_party/node'),
    ],
    hiddenimports=[],
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
    name='FluxoLoad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='assets/fluxoload-icon.ico',
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    Tree(
        r'C:\Users\gilma\bgutil-ytdlp-pot-provider\server',
        prefix='third_party/bgutil-ytdlp-pot-provider/server',
    ),
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FluxoLoad',
)
