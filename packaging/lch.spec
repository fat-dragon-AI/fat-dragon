# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：onedir；jieba 由 hook-jieba 自动收集
# 用法见 scripts/build_release.sh

block_cipher = None

a = Analysis(
    ['../lch/__main__.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
    hiddenimports=['jieba', 'jieba.posseg', 'jieba.analyse'],
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
    name='lch',
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
    upx_exclude=[],
    name='lch',
)
