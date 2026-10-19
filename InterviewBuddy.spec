# -*- mode: python ; coding: utf-8 -*-
import os
import stat
import shutil
from PyInstaller.utils.hooks import collect_all

# Prevent Windows/OneDrive PermissionError by unlocking and cleaning old dist output
def _unlock_and_clean_dist(folder):
    if not os.path.exists(folder):
        return
    try:
        os.chmod(folder, stat.S_IWRITE)
    except OSError:
        pass
    for root, dirs, files in os.walk(folder):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), stat.S_IWRITE)
            except OSError:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IWRITE)
            except OSError:
                pass
    def _on_err(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    try:
        shutil.rmtree(folder, onexc=_on_err)
    except TypeError:
        shutil.rmtree(folder, onerror=_on_err)
    except Exception:
        pass

def _unlock_build(folder):
    if not os.path.exists(folder):
        return
    try:
        os.chmod(folder, stat.S_IWRITE)
    except OSError:
        pass
    for root, dirs, files in os.walk(folder):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), stat.S_IWRITE)
            except OSError:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IWRITE)
            except OSError:
                pass

_unlock_and_clean_dist(os.path.join("dist", "InterviewBuddy"))
_unlock_build("build")

datas = [('style.css', '.')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('soundcard')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='InterviewBuddy',
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
    icon=['InterviewBuddy.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='InterviewBuddy',
)
