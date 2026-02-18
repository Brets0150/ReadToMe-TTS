@echo off
REM Build script for ReadToMe-TTS
REM Run this from the project root directory on Windows
REM
REM This script will:
REM   1. Set up a virtual environment and install dependencies (if needed)
REM   2. Build the portable .exe with PyInstaller (using a local temp directory)
REM   3. Install Inno Setup (if needed) and build the installer
REM

echo ============================================
echo  ReadToMe-TTS Build Script
echo ============================================
echo.

REM Check for at least one Piper voice model
dir /b "models\en_US-*.onnx" >nul 2>&1
if errorlevel 1 (
    echo ERROR: No Piper voice models found in models\
    echo Run .\download-voices.ps1 to download voices, or manually place .onnx files in models\
    exit /b 1
)

REM ── Step 1: Ensure virtual environment with all dependencies ────────────
echo [1/4] Checking build environment...
if not exist ".venv\Scripts\python.exe" (
    echo       Creating virtual environment...
    python -m venv .venv
)
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "VENV_PIP=.venv\Scripts\pip.exe"
set "VENV_PYINSTALLER=.venv\Scripts\pyinstaller.exe"

REM Install project + dev dependencies (pyinstaller) into venv
"%VENV_PIP%" install -e ".[dev]" --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    exit /b 1
)
echo       Build environment ready

REM ── Step 2: Build with PyInstaller to a local temp directory ───────────
REM Building to a local path avoids "Access is denied" errors that occur
REM when PyInstaller tries to clean files on network shares (UNC paths).
set "BUILD_TEMP=%TEMP%\ReadToMe-build"
set "BUILD_DIST=%BUILD_TEMP%\dist"
set "BUILD_WORK=%BUILD_TEMP%\build"

echo [2/4] Building with PyInstaller...
if exist "%BUILD_TEMP%" (
    echo       Cleaning previous build temp...
    rmdir /s /q "%BUILD_TEMP%" 2>nul
)
mkdir "%BUILD_TEMP%" 2>nul

"%VENV_PYINSTALLER%" readtome.spec --noconfirm --clean --distpath "%BUILD_DIST%" --workpath "%BUILD_WORK%"
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    exit /b 1
)
echo       PyInstaller build complete

REM Copy build output back to project dist/
echo       Copying build output to dist\...
if exist "dist\ReadToMe" rmdir /s /q "dist\ReadToMe" 2>nul
if exist "dist\ReadToMe" (
    REM Old dist still locked — rename it out of the way
    echo       Previous dist\ReadToMe locked, renaming...
    rename "dist\ReadToMe" "ReadToMe.old_%RANDOM%" 2>nul
)
if not exist "dist" mkdir dist
if not exist "dist\ReadToMe" (
    xcopy /s /e /i /q /y "%BUILD_DIST%\ReadToMe" "dist\ReadToMe" >nul
    if errorlevel 1 (
        echo WARNING: Could not copy to dist\ReadToMe
    ) else (
        echo       Portable build ready: dist\ReadToMe\ReadToMe.exe
    )
)
if not exist "dist\ReadToMe\ReadToMe.exe" (
    echo       NOTE: dist\ReadToMe was locked by another process.
    echo       Build output is at: %BUILD_DIST%\ReadToMe\ReadToMe.exe
    echo       Close any running ReadToMe.exe or Explorer windows, then
    echo       manually delete dist\ReadToMe and re-run build.bat.
)

REM ── Step 3: Ensure Inno Setup is installed ──────────────────────────────
echo [3/4] Checking for Inno Setup...
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        echo       Found Inno Setup at default location
    ) else (
        echo       Inno Setup not found. Downloading and installing...
        echo.
        powershell -Command "& { $url = 'https://files.jrsoftware.org/is/6/innosetup-6.4.3.exe'; $out = '%TEMP%\innosetup-6.4.3.exe'; if (-not (Test-Path $out)) { Write-Host '       Downloading Inno Setup 6.4.3...'; Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing }; Write-Host '       Installing Inno Setup (silent)...'; Start-Process -FilePath $out -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait; Write-Host '       Inno Setup installed.' }"
        if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
            echo ERROR: Inno Setup installation failed.
            echo       Download manually from https://jrsoftware.org/isinfo.php
            echo       The portable .exe is still available at: dist\ReadToMe\ReadToMe.exe
            exit /b 1
        )
    )
)

REM Determine ISCC path
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    set "ISCC_CMD=iscc"
) else (
    set "ISCC_CMD=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

REM ── Step 4: Build installer ─────────────────────────────────────────────
echo [4/4] Building installer with Inno Setup...
if not exist "dist\installer" mkdir dist\installer
"%ISCC_CMD%" installer\ReadToMe_Setup.iss
if errorlevel 1 (
    echo ERROR: Inno Setup build failed!
    exit /b 1
)
echo       Installer created: dist\installer\ReadToMe_Setup_0.2.0.exe

echo.
echo ============================================
echo  Build complete!
echo ============================================
echo.
echo  Portable:  dist\ReadToMe\ReadToMe.exe
if exist "dist\installer\ReadToMe_Setup_0.2.0.exe" (
    echo  Installer: dist\installer\ReadToMe_Setup_0.2.0.exe
)
echo.
