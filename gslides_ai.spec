# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for GSlides AI desktop app."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('src/gslides_ai', 'gslides_ai'),
    ],
    hiddenimports=[
        'flet',
        'flet_core',
        'flet_runtime',
        'gslides_ai',
        'gslides_ai.app',
        'gslides_ai.slides',
        'gslides_ai.auth',
        'gslides_ai.themes',
        'google.oauth2.credentials',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient.http',
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
    name='GSlides AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,  # Will build for current architecture
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GSlides AI',
)

app = BUNDLE(
    coll,
    name='GSlides AI.app',
    icon='assets/icon.png',
    bundle_identifier='com.snowflake.gslidesai',
    info_plist={
        'CFBundleName': 'GSlides AI',
        'CFBundleDisplayName': 'GSlides AI',
        'CFBundleGetInfoString': 'Create stunning Google Slides presentations',
        'CFBundleIdentifier': 'com.snowflake.gslidesai',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15.0',
        'NSHumanReadableCopyright': 'Copyright © 2026 Snowflake Inc. All rights reserved.',
    },
)
