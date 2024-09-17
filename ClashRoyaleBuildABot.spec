a = Analysis(
    ['main.py'],
    binaries=[],
    datas=[
        ('clashroyalebuildabot', 'clashroyalebuildabot'),
        ('clashroyalebuildabot/images/cards', 'clashroyalebuildabot/images/cards'),
        ('clashroyalebuildabot/images/screen', 'clashroyalebuildabot/images/screen'),
        ('clashroyalebuildabot/gui', 'clashroyalebuildabot/gui'),
        ('clashroyalebuildabot/models', 'clashroyalebuildabot/models'),
        ('clashroyalebuildabot/namespaces', 'clashroyalebuildabot/namespaces'),
        ('clashroyalebuildabot/utils', 'clashroyalebuildabot/utils')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClashRoyaleBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['clashroyalebuildabot\\images\\icon.ico'],
)
