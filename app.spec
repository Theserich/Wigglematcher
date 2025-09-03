# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE
import shutil

block_cipher = None

SPEC_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
LIB_DIR = SPEC_DIR / "Library"
DIST_DIR = SPEC_DIR / "dist"

datas = []

a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[],
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
    name='app.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    onefile=True
)
