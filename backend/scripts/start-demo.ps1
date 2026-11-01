<#
.SYNOPSIS
  Starts the SpeakWise backend and a free Cloudflare quick tunnel, then prints the public
  https:// address to paste into the app (Profile -> Server). Press Ctrl+C to stop both.

.EXAMPLE
  cd D:\madam_project\SpeakWise\backend
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
  .\scripts\start-demo.ps1
#>
param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$backendDir = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backendDir '.venv\Scripts\python.exe'
$logDir = Join-Path $backendDir 'data\logs'
New-Item -ItemType Directory -Force $logDir | Out-Null

function Test-Backend {
    try {
        Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/health" -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 1. Find cloudflared (installed with winget, or saved as backend\tools\cloudflared.exe).
$cloudflared = $null
$cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($cmd) { $cloudflared = $cmd.Source }
$localCopy = Join-Path $backendDir 'tools\cloudflared.exe'
if (-not $cloudflared -and (Test-Path $localCopy)) { $cloudflared = $localCopy }
if (-not $cloudflared) {
    Write-Host 'cloudflared was not found. Install it first (docs\SETUP_LOCAL_TUNNEL.md, step 2).' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $python)) {
    Write-Host "Python environment not found at $python (see backend\README.md, first-time setup)." -ForegroundColor Red
    exit 1
}

# 2. Start the backend unless it is already running.
$backendProc = $null
if (Test-Backend) {
    Write-Host "Backend already running on port $Port."
} else {
    Write-Host 'Starting backend...'
    $env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
    $backendProc = Start-Process -FilePath $python -PassThru -NoNewWindow `
        -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', "$Port" `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput (Join-Path $logDir 'backend.out.log') `
        -RedirectStandardError (Join-Path $logDir 'backend.log')
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Backend) { $ready = $true; break }
    }
    if (-not $ready) {
        Write-Host "Backend did not start. Check $logDir\backend.log" -ForegroundColor Red
        if ($backendProc) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
        exit 1
    }
    Write-Host 'Backend is up.'
}

# 3. Start the quick tunnel and wait for its public address.
$tunnelLog = Join-Path $logDir 'cloudflared.log'
Remove-Item $tunnelLog -ErrorAction SilentlyContinue
Write-Host 'Starting Cloudflare tunnel...'
$tunnelProc = Start-Process -FilePath $cloudflared -PassThru -NoNewWindow `
    -ArgumentList 'tunnel', '--no-autoupdate', '--url', "http://localhost:$Port" `
    -RedirectStandardOutput (Join-Path $logDir 'cloudflared.out.log') `
    -RedirectStandardError $tunnelLog

$url = $null
for ($i = 0; $i -lt 60 -and -not $url; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $tunnelLog) {
        $m = Select-String -Path $tunnelLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' | Select-Object -First 1
        if ($m) { $url = $m.Matches[0].Value }
    }
}

try {
    if (-not $url) {
        Write-Host "No tunnel address yet. Check $tunnelLog" -ForegroundColor Red
        exit 1
    }
    Set-Clipboard -Value $url
    Write-Host ''
    Write-Host '  SpeakWise is online at:' -ForegroundColor Green
    Write-Host "  $url" -ForegroundColor Green
    Write-Host '  (copied to clipboard) - paste it in the app: Profile -> Server -> Save & test'
    Write-Host "  Check in a browser: $url/health"
    Write-Host ''
    Write-Host '  Keep this window open. Press Ctrl+C to stop.'
    Wait-Process -Id $tunnelProc.Id
} finally {
    Stop-Process -Id $tunnelProc.Id -Force -ErrorAction SilentlyContinue
    if ($backendProc) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
    Write-Host 'Stopped.'
}
