# =============================================================================
# ReadToMe-TTS - Download All Piper English (US) Voices
# =============================================================================
#
# Downloads all available en_US voice models from Hugging Face into the
# models/ directory. Each voice requires two files: .onnx and .onnx.json
#
# Usage:
#   .\download-voices.ps1
#
# Source: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US
#

$ErrorActionPreference = "Stop"

$BaseUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
$ModelsDir = Join-Path $PSScriptRoot "models"

# All available en_US voices with their quality levels
$Voices = @(
    @{ Name = "amy";            Qualities = @("low", "medium") }
    @{ Name = "arctic";         Qualities = @("medium") }
    @{ Name = "bryce";          Qualities = @("medium") }
    @{ Name = "danny";          Qualities = @("low") }
    @{ Name = "hfc_female";     Qualities = @("medium") }
    @{ Name = "hfc_male";       Qualities = @("medium") }
    @{ Name = "joe";            Qualities = @("medium") }
    @{ Name = "john";           Qualities = @("medium") }
    @{ Name = "kathleen";       Qualities = @("low") }
    @{ Name = "kristin";        Qualities = @("medium") }
    @{ Name = "kusal";          Qualities = @("medium") }
    @{ Name = "l2arctic";       Qualities = @("medium") }
    @{ Name = "lessac";         Qualities = @("low", "medium", "high") }
    @{ Name = "libritts";       Qualities = @("high") }
    @{ Name = "libritts_r";     Qualities = @("medium") }
    @{ Name = "ljspeech";       Qualities = @("high", "medium") }
    @{ Name = "norman";         Qualities = @("medium") }
    @{ Name = "reza_ibrahim";   Qualities = @("medium") }
    @{ Name = "ryan";           Qualities = @("low", "medium", "high") }
    @{ Name = "sam";            Qualities = @("medium") }
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ReadToMe-TTS - Download All Voices" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Create models directory if needed
if (-not (Test-Path $ModelsDir)) {
    New-Item -ItemType Directory -Path $ModelsDir | Out-Null
}

# Count total downloads
$TotalFiles = 0
foreach ($Voice in $Voices) {
    $TotalFiles += $Voice.Qualities.Count
}
$summary = "  Found " + $Voices.Count + " voices, " + $TotalFiles + " model variants"
Write-Host $summary -ForegroundColor White
Write-Host "  Destination: $ModelsDir" -ForegroundColor White
Write-Host ""

$Downloaded = 0
$Skipped = 0
$Failed = 0

foreach ($Voice in $Voices) {
    foreach ($Quality in $Voice.Qualities) {
        $FileName = "en_US-" + $Voice.Name + "-" + $Quality
        $OnnxFile = $FileName + ".onnx"
        $JsonFile = $FileName + ".onnx.json"
        $OnnxPath = Join-Path $ModelsDir $OnnxFile
        $JsonPath = Join-Path $ModelsDir $JsonFile

        # Skip if both files already exist
        if ((Test-Path $OnnxPath) -and (Test-Path $JsonPath)) {
            Write-Host "  [SKIP] $FileName - already downloaded" -ForegroundColor DarkGray
            $Skipped++
            continue
        }

        $OnnxUrl = $BaseUrl + "/" + $Voice.Name + "/" + $Quality + "/" + $OnnxFile
        $JsonUrl = $BaseUrl + "/" + $Voice.Name + "/" + $Quality + "/" + $JsonFile

        Write-Host "  [DOWN] $FileName" -ForegroundColor Yellow -NoNewline

        try {
            if (-not (Test-Path $JsonPath)) {
                Invoke-WebRequest -Uri $JsonUrl -OutFile $JsonPath -UseBasicParsing
            }
            if (-not (Test-Path $OnnxPath)) {
                Invoke-WebRequest -Uri $OnnxUrl -OutFile $OnnxPath -UseBasicParsing
            }
            Write-Host "`r  [ OK ] $FileName" -ForegroundColor Green
            $Downloaded++
        }
        catch {
            $errMsg = $_.Exception.Message
            Write-Host "`r  [FAIL] $FileName - $errMsg" -ForegroundColor Red
            # Clean up partial downloads
            if (Test-Path $OnnxPath) { Remove-Item $OnnxPath -ErrorAction SilentlyContinue }
            if (Test-Path $JsonPath) { Remove-Item $JsonPath -ErrorAction SilentlyContinue }
            $Failed++
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Download Complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Downloaded: $Downloaded" -ForegroundColor Green
Write-Host "  Skipped:    $Skipped" -ForegroundColor DarkGray
if ($Failed -gt 0) {
    Write-Host "  Failed:     $Failed" -ForegroundColor Red
}
Write-Host ""
Write-Host "  Voices are ready in: $ModelsDir" -ForegroundColor White
Write-Host "  Restart ReadToMe to see them in the Voice menu." -ForegroundColor White
Write-Host ""
