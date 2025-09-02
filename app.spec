# app.spec
# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
# Note: no Tree import needed for Analysis.datas

block_cipher = None

SPEC_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
LIB_DIR = SPEC_DIR / "Library"

# datas must be a list of 2-tuples: (source_path, target_dir_inside_dist)
datas = []
if LIB_DIR.is_dir():
    datas.append((str(LIB_DIR), 'Library'))

a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,                 # <-- Correct format
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
    name='app',                  # app.exe inside dist/app/
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='app',                  # dist/app/
)
