# QueryMind setup and execution script for Windows PowerShell

[CmdletBinding()]
param (
    [switch]$Train,
    [alias("epoch")][int]$Epochs = 50,
    [switch]$Test,
    [string]$Query = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "      QueryMind - Query Optimizer Setup and Run   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Virtual Environment Setup
$VenvDir = ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "[+] Creating Python virtual environment in $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

# 2. Activation
Write-Host "[+] Activating virtual environment..." -ForegroundColor Green
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    $env:PATH = "$(Get-Location)\$VenvDir\Scripts;$env:PATH"
}

# 3. Dependency Installation
Write-Host "[+] Checking and installing dependencies from requirements.txt..." -ForegroundColor Green
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

# 4. Construct CLI Arguments
$cliArgs = @()

# Also check raw $args in case user typed --train or --test
foreach ($arg in $args) {
    if ($arg -eq "--train") { $Train = $true }
    if ($arg -eq "--test")  { $Test = $true }
}

if ($Train) {
    $cliArgs += "--train"
    $cliArgs += "--epochs"
    $cliArgs += $Epochs
}
elseif ($Test) {
    $cliArgs += "--test"
}
elseif ($Query -ne "") {
    $cliArgs += "--query"
    $cliArgs += "$Query"
}

Write-Host "[+] Executing QueryMind..." -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Gray
python cli.py $cliArgs
Write-Host "==================================================" -ForegroundColor Cyan
