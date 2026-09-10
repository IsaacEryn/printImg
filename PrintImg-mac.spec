# -*- mode: python ; coding: utf-8 -*-
# macOS 빌드용. 맥에서 `scripts/build.sh`로 실행한다. 결과: dist/PrintImg.app

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['win32ui', 'win32print', 'win32con'],
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
    name='PrintImg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='PrintImg.app',
    icon=None,
    bundle_identifier='com.codeslog.printimg',
    info_plist={
        'CFBundleDisplayName': 'PrintImg',
        'CFBundleShortVersionString': '1.1.0',
        'NSHighResolutionCapable': True,
    },
)
