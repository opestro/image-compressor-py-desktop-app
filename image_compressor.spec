# -*- mode: python ; coding: utf-8 -*-
import os
import site
import tkinterdnd2

# Get tkdnd library path
tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

block_cipher = None

a = Analysis(
    ['image_compressor.py'],
    pathex=[],
    binaries=[],
    datas=[
        (tkdnd_path, 'tkinterdnd2/tkdnd'),  # Include tkdnd library files
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinterdnd2',
        'humanize',
        'piexif'
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

# Add tkdnd library files
tkdnd_files = []
for root, dirs, files in os.walk(tkdnd_path):
    for file in files:
        source = os.path.join(root, file)
        dest = os.path.join('tkinterdnd2/tkdnd', os.path.relpath(source, tkdnd_path))
        tkdnd_files.append((source, dest))

a.datas += tkdnd_files

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImageCompressor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 