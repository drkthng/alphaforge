# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('streamlit')
datas += collect_data_files('plotly')
datas += collect_data_files('alphaforge')
datas += [('assets/icon.png', 'assets')]
datas += [('dashboard', 'dashboard')]

hiddenimports = [
    'streamlit',
    'plotly',
    'pyarrow',
    'sqlalchemy',
    'pydantic',
    'pystray',
    'PIL',
    'alphaforge',
    'alphaforge.analysis',
    'alphaforge.analysis.custom_metrics',
    'alphaforge.analysis.heatmap',
    'win32timezone'
]

a = Analysis(
    ['src/alphaforge/launcher.pyw'],
    pathex=['src', 'dashboard'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'data'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AlphaForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AlphaForge',
)
