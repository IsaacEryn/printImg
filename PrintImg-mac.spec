# -*- mode: python ; coding: utf-8 -*-
# macOS 빌드용. 맥에서 `scripts/build.sh`로 실행한다. 결과: dist/PrintImg.app
# .app 번들은 onedir로 만든다. onefile + BUNDLE 조합은 PyInstaller 6에서 deprecated이고
# (7에서 오류), 부트로더와 실제 앱이 두 프로세스로 떠서 실행마다 임시 폴더에 풀어야 한다.

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
    [],
    exclude_binaries=True,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='PrintImg',
)

app = BUNDLE(
    coll,
    name='PrintImg.app',
    icon=None,
    bundle_identifier='com.codeslog.printimg',
    info_plist={
        'CFBundleDisplayName': 'PrintImg',
        'CFBundleShortVersionString': '1.1.0',
        'NSHighResolutionCapable': True,
    },
)
