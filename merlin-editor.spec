# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Merlin Editor (macOS / Linux / Windows)."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Pick up a bundled ffmpeg if the build pipeline placed one in bin/.
ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
ffmpeg_src = Path("bin") / ffmpeg_name
bundled_binaries = []
bundled_datas = []
if ffmpeg_src.is_file():
    bundled_binaries.append((str(ffmpeg_src), "."))
if Path("THIRD_PARTY_NOTICES.md").is_file():
    bundled_datas.append(("THIRD_PARTY_NOTICES.md", "."))

# Exclude Qt modules we don't use to shave ~80MB off the bundle.
excluded_qt = [
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtNetwork",
    "PySide6.QtNfc",
    "PySide6.QtOpcUa",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
]

a = Analysis(
    ["merlin_gui/app.py"],
    pathex=[],
    binaries=bundled_binaries,
    datas=bundled_datas,
    hiddenimports=collect_submodules("PySide6.QtMultimedia"),
    hookspath=[],
    runtime_hooks=[],
    excludes=excluded_qt,
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
    name="merlin-editor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="merlin-editor",
)
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Merlin Editor.app",
        icon=None,
        bundle_identifier="com.merlin.editor",
        version="0.1.0",
        info_plist={
            "CFBundleName": "Merlin Editor",
            "CFBundleDisplayName": "Merlin Editor",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "MIT — built on IArchi/Merlin-jailbreak",
        },
    )
