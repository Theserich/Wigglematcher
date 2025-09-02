
# app.spec
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import Tree

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],                             # build from repo root
    binaries=[],
    datas=Tree('Library', prefix='Library'),  # <- include whole Library/ dir
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app',            # <- executable name (dist/app/app.exe)
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # set True only if UPX is installed
    console=False          # set True if you want a console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='app'             # <- output folder name (dist/app/)
)
