# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for ReadToMe-TTS (Piper TTS)
# Build with: pyinstaller readtome.spec

import os
from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
)

block_cipher = None
project_root = os.path.abspath(".")

# Collect packages that bundle native binaries or data files.
extra_datas = []
extra_binaries = []
extra_hiddenimports = []

# Piper TTS — collect everything (small package)
try:
    d, b, h = collect_all("piper")
    extra_datas += d
    extra_binaries += b
    extra_hiddenimports += h
except Exception:
    pass

# piper_phonemize — may be a native extension, not a Python package.
# On Windows it's typically bundled as DLLs alongside piper, so we just
# collect its dynamic libs if available. No collect_all (it's not a package).
try:
    extra_binaries += collect_dynamic_libs("piper_phonemize")
except Exception:
    pass

# onnxruntime — only collect the native runtime DLLs and core data files.
# Do NOT use collect_all() which pulls in hundreds of unnecessary submodules
# (transformers, tools, quantization, etc.) that bloat the build massively.
try:
    extra_datas += collect_data_files("onnxruntime")
    extra_binaries += collect_dynamic_libs("onnxruntime")
except Exception:
    pass

a = Analysis(
    [os.path.join("readtome", "__main__.py")],
    pathex=[project_root],
    binaries=extra_binaries,
    datas=[
        # Bundled Piper voice models (medium quality)
        (os.path.join("models", "en_US-amy-medium.onnx"), "models"),
        (os.path.join("models", "en_US-amy-medium.onnx.json"), "models"),
        (os.path.join("models", "en_US-kristin-medium.onnx"), "models"),
        (os.path.join("models", "en_US-kristin-medium.onnx.json"), "models"),
        (os.path.join("models", "en_US-kusal-medium.onnx"), "models"),
        (os.path.join("models", "en_US-kusal-medium.onnx.json"), "models"),
        (os.path.join("models", "en_US-ryan-medium.onnx"), "models"),
        (os.path.join("models", "en_US-ryan-medium.onnx.json"), "models"),
        # Tray icon resources
        (os.path.join("readtome", "resources"), os.path.join("readtome", "resources")),
    ] + extra_datas,
    hiddenimports=[
        "piper",
        "piper.voice",
        "piper.config",
        "onnxruntime",
        "onnxruntime.capi",
        "onnxruntime.capi.onnxruntime_pybind11_state",
        "sounddevice",
        "_sounddevice_data",
        "keyboard",
        "pyperclip",
        "pystray",
        "PIL",
        "numpy",
    ] + extra_hiddenimports,
    hookspath=[os.path.join(project_root, "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "pytest",
        "setuptools",
        "pip",
        # Exclude onnxruntime subpackages not needed for inference
        "onnxruntime.transformers",
        "onnxruntime.tools",
        "onnxruntime.quantization",
        "onnxruntime.training",
    ],
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
    name="ReadToMe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — runs as tray app
    disable_windowed_traceback=False,
    icon=os.path.join("readtome", "resources", "icon.ico")
    if os.path.exists(os.path.join("readtome", "resources", "icon.ico"))
    else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ReadToMe",
)
