# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import Tree

block_cipher = None

# Be resilient when __file__ isn't defined by PyInstaller
SPEC_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
LIB_DIR = SPEC_DIR / "Library"

# Collect all files in Library/ into bundle under Library/ (preserve structure)
datas = []
if LIB_DIR.is_dir():
    datas += Tree(str(LIB_DIR), prefix='Library').toc

a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[]
    ,excludes=[]
    ,noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Keep positional [] for exclude_binaries to avoid arg shifting across versions
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
    upx=False,       # set True only if UPX is installed on your runner
    console=False    # True for console app
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,       # match UPX setting above
    name='app'
)
