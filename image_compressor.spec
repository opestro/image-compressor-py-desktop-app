# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site
import platform

# Handle tkinterdnd2 import more robustly
try:
    import tkinterdnd2
    tkinterdnd2_path = os.path.dirname(tkinterdnd2.__file__)
    tkdnd_base_path = os.path.join(tkinterdnd2_path, 'tkdnd')
    
    # Determine the correct platform directory
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'darwin':
        if 'arm' in machine or 'aarch64' in machine:
            platform_dir = 'osx-arm64'
        else:
            platform_dir = 'osx-x64'
    elif system == 'windows':
        if 'arm' in machine or 'aarch64' in machine:
            platform_dir = 'win-arm64'
        elif '64' in machine:
            platform_dir = 'win-x64'
        else:
            platform_dir = 'win-x86'
    else:  # Linux
        if 'arm' in machine or 'aarch64' in machine:
            platform_dir = 'linux-arm64'
        else:
            platform_dir = 'linux-x64'
    
    platform_tkdnd_path = os.path.join(tkdnd_base_path, platform_dir)
    
    if os.path.exists(platform_tkdnd_path):
        tkdnd_data = [
            (tkdnd_base_path, 'tkinterdnd2/tkdnd'),  # Include base directory
            (platform_tkdnd_path, f'tkinterdnd2/tkdnd/{platform_dir}'),  # Include platform-specific files
        ]
        
        # Also include the shared library as a binary
        tkdnd_binaries = []
        if system == 'darwin':
            dylib_path = os.path.join(platform_tkdnd_path, 'libtkdnd2.9.3.dylib')
            if os.path.exists(dylib_path):
                tkdnd_binaries.append((dylib_path, f'tkinterdnd2/tkdnd/{platform_dir}'))
        elif system == 'windows':
            dll_path = os.path.join(platform_tkdnd_path, 'tkdnd29.dll')
            if os.path.exists(dll_path):
                tkdnd_binaries.append((dll_path, f'tkinterdnd2/tkdnd/{platform_dir}'))
        else:  # Linux
            so_path = os.path.join(platform_tkdnd_path, 'libtkdnd2.9.3.so')
            if os.path.exists(so_path):
                tkdnd_binaries.append((so_path, f'tkinterdnd2/tkdnd/{platform_dir}'))
        
        print(f"Including tkdnd files from: {platform_tkdnd_path}")
        print(f"Including tkdnd binaries: {tkdnd_binaries}")
    else:
        print(f"Warning: Platform-specific tkdnd directory not found: {platform_tkdnd_path}")
        tkdnd_data = [(tkdnd_base_path, 'tkinterdnd2/tkdnd')]
        tkdnd_binaries = []
        
except ImportError:
    print("Warning: tkinterdnd2 not found, drag-and-drop may not work")
    tkdnd_data = []
    tkdnd_binaries = []

block_cipher = None

# Define platform-specific settings
if sys.platform == 'win32':
    icon_file = 'assets/logo.ico'
    console_mode = False
elif sys.platform == 'darwin':
    icon_file = 'assets/logo.ico'
    console_mode = False
else:  # Linux
    icon_file = None
    console_mode = False

a = Analysis(
    ['image_compressor.py'],
    pathex=[],
    binaries=tkdnd_binaries,  # Add tkdnd binaries
    datas=[
        *tkdnd_data,  # Add tkdnd data if available
        ('assets/logo.png', 'assets'),  # Add logo file
    ] + ([('assets/logo.ico', '.')] if os.path.exists('assets/logo.ico') else []),
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinterdnd2',
        'humanize',
        'piexif',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ImageCompressor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console_mode,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageCompressor',
)

app = BUNDLE(
    coll,
    name='ImageCompressor.app',
    icon='assets/logo.ico',
    bundle_identifier='com.mehdiharzallah.imagecompressor',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image',
                'CFBundleTypeIconFile': 'logo.ico',
                'LSItemContentTypes': [
                    'public.image',
                    'public.png',
                    'public.jpeg',
                    'public.webp',
                ],
                'LSHandlerRank': 'Alternate',
            }
        ],
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.graphics-design',
        'NSHumanReadableCopyright': '© 2024 MEHDI HARZALLAH',
        'LSMinimumSystemVersion': '10.15.0',
    },
) 