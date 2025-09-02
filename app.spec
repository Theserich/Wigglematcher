# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import Tree

block_cipher = None

# Be resilient if __file__ is not defined when PyInstaller executes the spec
SPEC_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
LIB_DIR = SPEC_DIR / "Library"

# Pass Tree(...) directly; no ".toc" attribute
datas = []
if LIB_DIR.is_dir():
    datas += Tree(str(LIB_DIR), prefix='Library')

a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Keep the explicit [] for exclude_binaries to avoid positional arg shifts
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # set True only if UPX is installed on the runner
    console=False,    # True for a console app
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='app',
)
