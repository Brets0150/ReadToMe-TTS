# =============================================================================
# ReadToMe-TTS - Developer Setup & Launch
# =============================================================================
#
# Complete developer setup script. Creates a virtual environment, installs all
# dependencies (including build tools), downloads the 4 bundled voice models,
# ensures Inno Setup is available for building the installer, and launches
# ReadToMe in debug mode.
#
# After running this script once, you can:
#   - Run the app:       .venv\Scripts\python.exe -m readtome --debug
#   - Build installer:   .\build.bat
#   - Download all 20+   .\download-voices.ps1
#     US English voices
#
# Usage:
#   .\run-dev.ps1              # Full setup + launch in debug mode
#   .\run-dev.ps1 -NoBuild     # Skip Inno Setup check
#   .\run-dev.ps1 -NoLaunch    # Setup only, don't launch the app
#

param(
    [switch]$NoBuild,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$VenvDir = Join-Path $ProjectDir ".venv"
$ModelsDir = Join-Path $ProjectDir "models"

# The 4 bundled voices (medium quality)
$BundledVoices = @(
    @{ Name = "amy";     Folder = "amy";     Quality = "medium" }
    @{ Name = "kristin"; Folder = "kristin"; Quality = "medium" }
    @{ Name = "kusal";   Folder = "kusal";   Quality = "medium" }
    @{ Name = "ryan";    Folder = "ryan";    Quality = "medium" }
)

$BaseUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"

$StepCount = 4
if (-not $NoBuild) { $StepCount = 5 }

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ReadToMe-TTS - Developer Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Create virtual environment ────────────────────────────────────
$step = 1
if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
    Write-Host "[$step/$StepCount] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        Write-Host "       Make sure Python 3.10+ is installed and on your PATH." -ForegroundColor Red
        exit 1
    }
    Write-Host "      Created: $VenvDir" -ForegroundColor Green
} else {
    Write-Host "[$step/$StepCount] Virtual environment exists" -ForegroundColor Green
}

# ── Step 2: Install all dependencies (including dev/build tools) ──────────
$step = 2
Write-Host "[$step/$StepCount] Installing dependencies..." -ForegroundColor Yellow
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
& $PipExe install -e ".[dev]" --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Retrying with verbose output..." -ForegroundColor Yellow
    & $PipExe install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}
Write-Host "      All packages installed (piper-tts, sounddevice, pyinstaller, etc.)" -ForegroundColor Green

# ── Step 3: Download the 4 bundled voice models ──────────────────────────
$step = 3
if (-not (Test-Path $ModelsDir)) {
    New-Item -ItemType Directory -Path $ModelsDir | Out-Null
}

$allPresent = $true
foreach ($Voice in $BundledVoices) {
    $fileName = "en_US-$($Voice.Name)-$($Voice.Quality)"
    $onnxPath = Join-Path $ModelsDir ($fileName + ".onnx")
    $jsonPath = Join-Path $ModelsDir ($fileName + ".onnx.json")
    if (-not ((Test-Path $onnxPath) -and (Test-Path $jsonPath))) {
        $allPresent = $false
        break
    }
}

if ($allPresent) {
    $voiceNames = ($BundledVoices | ForEach-Object { $_.Name }) -join ", "
    Write-Host "[$step/$StepCount] All 4 bundled voices present ($voiceNames)" -ForegroundColor Green
} else {
    Write-Host "[$step/$StepCount] Downloading bundled voice models..." -ForegroundColor Yellow
    foreach ($Voice in $BundledVoices) {
        $fileName = "en_US-$($Voice.Name)-$($Voice.Quality)"
        $onnxFile = $fileName + ".onnx"
        $jsonFile = $fileName + ".onnx.json"
        $onnxPath = Join-Path $ModelsDir $onnxFile
        $jsonPath = Join-Path $ModelsDir $jsonFile

        if ((Test-Path $onnxPath) -and (Test-Path $jsonPath)) {
            Write-Host "      [SKIP] $fileName (already downloaded)" -ForegroundColor DarkGray
            continue
        }

        $voiceUrl = "$BaseUrl/$($Voice.Folder)/$($Voice.Quality)"
        Write-Host "      [DOWN] $fileName ..." -ForegroundColor Yellow -NoNewline

        try {
            if (-not (Test-Path $jsonPath)) {
                Invoke-WebRequest -Uri "$voiceUrl/$jsonFile" -OutFile $jsonPath -UseBasicParsing
            }
            if (-not (Test-Path $onnxPath)) {
                Invoke-WebRequest -Uri "$voiceUrl/$onnxFile" -OutFile $onnxPath -UseBasicParsing
            }
            Write-Host "`r      [ OK ] $fileName                    " -ForegroundColor Green
        }
        catch {
            Write-Host "`r      [FAIL] $fileName - $($_.Exception.Message)" -ForegroundColor Red
            if (Test-Path $onnxPath) { Remove-Item $onnxPath -ErrorAction SilentlyContinue }
            if (Test-Path $jsonPath) { Remove-Item $jsonPath -ErrorAction SilentlyContinue }
        }
    }
}

# ── Step 4: Check for Inno Setup (needed to build the installer) ─────────
$step = 4
if (-not $NoBuild) {
    $isccFound = $false
    $isccPath = ""

    # Check PATH first
    $isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($isccCmd) {
        $isccFound = $true
        $isccPath = $isccCmd.Source
    }
    # Check default install location
    elseif (Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe") {
        $isccFound = $true
        $isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    }

    if ($isccFound) {
        Write-Host "[$step/$StepCount] Inno Setup found: $isccPath" -ForegroundColor Green
    } else {
        Write-Host "[$step/$StepCount] Inno Setup not found. Installing..." -ForegroundColor Yellow
        $installerUrl = "https://files.jrsoftware.org/is/6/innosetup-6.4.3.exe"
        $installerPath = Join-Path $env:TEMP "innosetup-6.4.3.exe"

        if (-not (Test-Path $installerPath)) {
            Write-Host "      Downloading Inno Setup 6.4.3..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        }

        Write-Host "      Installing Inno Setup (silent)..." -ForegroundColor Yellow
        Start-Process -FilePath $installerPath -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait

        if (Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe") {
            Write-Host "      Inno Setup installed successfully" -ForegroundColor Green
        } else {
            Write-Host "      WARNING: Inno Setup installation may have failed." -ForegroundColor Red
            Write-Host "      You can still run the app, but build.bat won't create an installer." -ForegroundColor Red
            Write-Host "      Download manually from: https://jrsoftware.org/isinfo.php" -ForegroundColor Red
        }
    }
    $step = 5
}

# ── Final Step: Launch in debug mode ──────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Setup Complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Count available voices
$voiceCount = (Get-ChildItem -Path $ModelsDir -Filter "*.onnx" -ErrorAction SilentlyContinue).Count
Write-Host "  Voice models:  $voiceCount found in models/" -ForegroundColor White
Write-Host "  Virtual env:   $VenvDir" -ForegroundColor White
Write-Host ""
Write-Host "  Run app:       .venv\Scripts\python.exe -m readtome --debug" -ForegroundColor White
Write-Host "  Build exe:     .\build.bat" -ForegroundColor White
Write-Host "  More voices:   .\download-voices.ps1" -ForegroundColor White
Write-Host ""

if (-not $NoLaunch) {
    Write-Host "[$step/$StepCount] Launching ReadToMe in debug mode..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
    Write-Host ""

    $PythonExe = Join-Path $VenvDir "Scripts\python.exe"
    & $PythonExe -m readtome --debug
} else {
    Write-Host "  Skipping launch (use -NoLaunch to setup only)." -ForegroundColor DarkGray
}
