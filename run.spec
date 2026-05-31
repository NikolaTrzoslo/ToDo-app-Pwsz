# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_dir = Path(SPECPATH)
png_files = [
    ('04-sfa_-temporary-tasks.png', '.'),
    ('add-96.png', '.'),
    ('add-new-3.png', '.'),
    ('correct-check.png', '.'),
    ('delete-851.png', '.'),
    ('edit-644.png', '.'),
    ('save-39.png', '.'),
    ('to-do-list-8.png', '.'),
]


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('Main.ui', '.'), ('Form.ui', '.')] + [
        (str(project_dir / filename), target) for filename, target in png_files
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
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
