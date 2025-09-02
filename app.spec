# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import Tree
import os

block_cipher = None

# Ensure 'Library' exists relative to the spec file.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LIB_DIR = os.path.join(BASE_DIR, "Library")

datas = []
if os.path.isdir(LIB_DIR):
    # Use .toc to ensure we pass a plain TOC (list of tuples), not a Tree object.
    datas += Tree(LIB_DIR, prefix='Library').toc

a = Analysis(
    ['main.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Note the empty list [] for exclude_binaries to keep argument positions unambiguous across PyInstaller versions.
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
    upx=True,         # set to False if you don't have UPX installed
    console=False,    # True for console app
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,         # set to False if you don't have UPX installed
    name='app'
)
