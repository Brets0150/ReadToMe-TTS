@echo off
setlocal enabledelayedexpansion
REM Build script for ReadToMe-TTS
REM Run this from the project root directory on Windows
REM
REM This script will:
REM   1. Set up a virtual environment and install dependencies (if needed)
REM   2. Build the portable .exe with PyInstaller (using a local temp directory)
REM   3. Create portable zip files (full + lite)
REM   4. Download the VC++ Redistributable (bundled in the installer)
REM   5. Install Inno Setup (if needed)
REM   6. Build the Windows installer
REM

echo ============================================
echo  ReadToMe-TTS Build Script
echo ============================================
echo.

REM -- Required Python version ------------------------------------------------
REM Python 3.14+ has known NumPy compatibility issues that cause the built
REM executable to crash on target systems. We require Python 3.12.x for
REM stable, widely-compatible builds.
set "REQUIRED_PY_MAJOR=3"
set "REQUIRED_PY_MINOR=12"

REM -- Read version from pyproject.toml ---------------------------------------
for /f "tokens=2 delims==""" %%V in ('findstr /c:"version = " pyproject.toml') do (
    set "APP_VERSION=%%V"
    goto :got_version
)
:got_version
REM Trim any surrounding quotes/spaces
set "APP_VERSION=%APP_VERSION: =%"
echo       Version: %APP_VERSION%

REM Check for at least one Piper voice model
dir /b "models\en_US-*.onnx" >nul 2>&1
if errorlevel 1 (
    echo ERROR: No Piper voice models found in models\
    echo Run .\download-voices.ps1 to download voices, or manually place .onnx files in models\
    exit /b 1
)

REM -- Step 1: Ensure virtual environment with all dependencies ----------------
echo [1/6] Checking build environment...
if not exist ".venv\Scripts\python.exe" (
    echo       Creating virtual environment with Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR%...
    REM Try the py launcher first (standard on Windows), then fall back to python
    set "PY_FOUND=0"
    py -%REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% --version >nul 2>&1
    if not errorlevel 1 (
        py -%REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% -m venv .venv 2>nul
        if not errorlevel 1 set "PY_FOUND=1"
    )
    if "!PY_FOUND!"=="0" (
        echo.
        echo       Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% is not installed on this system.
        echo.
        set /p "INSTALL_PY=      Would you like to download and install Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% now? (Y/N): "
        if /i "!INSTALL_PY!"=="Y" (
            set "PY_INSTALLER=%TEMP%\python-3.12.8-amd64.exe"
            if not exist "!PY_INSTALLER!" (
                echo       Downloading Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR%...
                powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '!PY_INSTALLER!' -UseBasicParsing"
            )
            echo       Installing Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% ^(this may take a minute^)...
            "!PY_INSTALLER!" /passive InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0
            REM Refresh PATH
            for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=%%B;%PATH%"
            echo       Python installed. Retrying venv creation...
            py -%REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% -m venv .venv 2>nul
            if errorlevel 1 (
                echo ERROR: Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% installation failed or was cancelled.
                echo       Install manually from https://www.python.org/downloads/
                exit /b 1
            )
        ) else (
            echo       Install Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% from https://www.python.org/downloads/
            exit /b 1
        )
    )
)

REM Verify the venv Python version is correct
for /f "tokens=2 delims= " %%V in ('".venv\Scripts\python.exe" --version 2^>^&1') do set "VENV_PY_VER=%%V"
echo       Python version: %VENV_PY_VER%
echo %VENV_PY_VER% | findstr /b "%REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR%." >nul
if errorlevel 1 (
    echo ERROR: Virtual environment has Python %VENV_PY_VER%, but %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR%.x is required.
    echo       Delete .venv and re-run build.bat to recreate it with the correct version.
    echo       Install Python %REQUIRED_PY_MAJOR%.%REQUIRED_PY_MINOR% from https://www.python.org/downloads/
    exit /b 1
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

REM -- Step 2: Build with PyInstaller to a local temp directory ----------------
REM Building to a local path avoids "Access is denied" errors that occur
REM when PyInstaller tries to clean files on network shares (UNC paths).
set "BUILD_TEMP=%TEMP%\ReadToMe-build"
set "BUILD_DIST=%BUILD_TEMP%\dist"
set "BUILD_WORK=%BUILD_TEMP%\build"

echo [2/6] Building with PyInstaller...
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
    REM Old dist still locked -- rename it out of the way
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

REM -- Step 3: Create portable zip files --------------------------------------
echo [3/6] Creating portable zip files...
set "ZIP_FULL=dist\ReadToMe_Portable_%APP_VERSION%.zip"
set "ZIP_LITE=dist\ReadToMe_Portable_lite_%APP_VERSION%.zip"

REM Delete previous zips if they exist
if exist "%ZIP_FULL%" del /q "%ZIP_FULL%"
if exist "%ZIP_LITE%" del /q "%ZIP_LITE%"

REM Full portable zip (all 4 voices)
echo       Creating full portable zip...
powershell -Command "Compress-Archive -Path 'dist\ReadToMe\*' -DestinationPath '%ZIP_FULL%' -CompressionLevel Optimal"
if exist "%ZIP_FULL%" (
    echo       Full zip: %ZIP_FULL%
) else (
    echo WARNING: Failed to create full portable zip
)

REM Lite portable zip (kristin voice only)
echo       Creating lite portable zip...
set "LITE_TEMP=%TEMP%\ReadToMe-lite"
if exist "%LITE_TEMP%" rmdir /s /q "%LITE_TEMP%" 2>nul

REM Copy entire build output
xcopy /s /e /i /q /y "dist\ReadToMe\*" "%LITE_TEMP%\ReadToMe" >nul
REM Remove all voice models from the lite copy (PyInstaller puts them in _internal\models\)
del /q "%LITE_TEMP%\ReadToMe\_internal\models\en_US-*.onnx" 2>nul
del /q "%LITE_TEMP%\ReadToMe\_internal\models\en_US-*.onnx.json" 2>nul
REM Copy back only kristin
copy /y "dist\ReadToMe\_internal\models\en_US-kristin-medium.onnx" "%LITE_TEMP%\ReadToMe\_internal\models\" >nul
copy /y "dist\ReadToMe\_internal\models\en_US-kristin-medium.onnx.json" "%LITE_TEMP%\ReadToMe\_internal\models\" >nul

powershell -Command "Compress-Archive -Path '%LITE_TEMP%\ReadToMe\*' -DestinationPath '%ZIP_LITE%' -CompressionLevel Optimal"
if exist "%ZIP_LITE%" (
    echo       Lite zip: %ZIP_LITE%
) else (
    echo WARNING: Failed to create lite portable zip
)
rmdir /s /q "%LITE_TEMP%" 2>nul

REM -- Step 4: Download VC++ Redistributable -----------------------------------
echo [4/6] Checking for VC++ Redistributable...
if not exist "redist" mkdir redist
if not exist "redist\vc_redist.x64.exe" (
    echo       Downloading Microsoft Visual C++ Redistributable...
    powershell -Command "& { Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'redist\vc_redist.x64.exe' -UseBasicParsing }"
    if not exist "redist\vc_redist.x64.exe" (
        echo ERROR: Failed to download VC++ Redistributable.
        echo       Download manually from https://aka.ms/vs/17/release/vc_redist.x64.exe
        echo       and place it in the redist\ directory.
        exit /b 1
    )
    echo       VC++ Redistributable downloaded
) else (
    echo       VC++ Redistributable already present
)

REM -- Step 5: Ensure Inno Setup is installed ----------------------------------
echo [5/6] Checking for Inno Setup...
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

REM -- Step 6: Build installer -------------------------------------------------
echo [6/6] Building installer with Inno Setup...
if not exist "dist\installer" mkdir dist\installer
"%ISCC_CMD%" installer\ReadToMe_Setup.iss
if errorlevel 1 (
    echo ERROR: Inno Setup build failed!
    exit /b 1
)
echo       Installer created: dist\installer\ReadToMe_Setup_%APP_VERSION%.exe

echo.
echo ============================================
echo  Build complete!
echo ============================================
echo.
echo  Portable:       dist\ReadToMe\ReadToMe.exe
if exist "%ZIP_FULL%" (
    echo  Portable zip:   %ZIP_FULL%
)
if exist "%ZIP_LITE%" (
    echo  Portable lite:  %ZIP_LITE%
)
if exist "dist\installer\ReadToMe_Setup_%APP_VERSION%.exe" (
    echo  Installer:      dist\installer\ReadToMe_Setup_%APP_VERSION%.exe
)
echo.
