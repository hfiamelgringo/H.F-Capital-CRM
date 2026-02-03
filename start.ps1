# Start CRM dashboard (Waitress). Used by winsw.
$ErrorActionPreference = "Stop"
$logDir = "C:\serve\H.F-Capital-CRM\logs"
$logFile = "$logDir\dashboard-service.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Log { param($msg) "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File $logFile -Append }
Log "=== Start ==="
Log "Running as: $env:USERNAME ($env:USERPROFILE)"

# Conda base: C:\ProgramData\miniconda3 — dashboard env Python:
$CondaPython = "C:\ProgramData\miniconda3\envs\dashboard\python.exe"
$try = @(
    $CondaPython,
    "C:\Users\Administrator\miniconda3\envs\dashboard\python.exe",
    "C:\ProgramData\anaconda3\envs\dashboard\python.exe",
    "$env:USERPROFILE\miniconda3\envs\dashboard\python.exe",
    "$env:USERPROFILE\anaconda3\envs\dashboard\python.exe",
    "C:\miniconda3\envs\dashboard\python.exe",
    "C:\anaconda3\envs\dashboard\python.exe"
)
foreach ($p in $try) {
    if ($p -and (Test-Path -LiteralPath $p)) { $CondaPython = $p; break }
}
if (-not $CondaPython) {
    Log "ERROR: Python not found. Edit start.ps1 and set `$CondaPython to the full path from: conda activate dashboard; (Get-Command python).Source"
    exit 1
}
Log "Python: $CondaPython"

# Subpath when behind nginx at /dashboard/ (leave empty if served at root)
$env:DJANGO_SCRIPT_NAME = "/dashboard"
# Server mode: turns off Django DEBUG. To turn DEBUG on on the server, comment out next line and restart service (see DEPLOY.md).
$env:DJANGO_PRODUCTION = "True"
# Avoid OSError on flush when run as service (no console); Python redirects internally
$env:RUN_SERVER_LOG = $logFile
Set-Location "C:\serve\H.F-Capital-CRM"
Log "CWD: $(Get-Location)"

# Run Python; capture all output so service failures show in log
try {
    & $CondaPython -u run_server.py *>> $logFile 2>&1
} catch {
    Log "ERROR: $($_.Exception.Message)"
    exit 1
}
$exitCode = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } else { 0 }
Log "Exit code: $exitCode"
exit $exitCode
