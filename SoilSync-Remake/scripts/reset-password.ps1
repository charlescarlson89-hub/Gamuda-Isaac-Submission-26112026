param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 2147483647)]
    [int]$UserId
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$backendRoot = Join-Path $projectRoot 'backend'
$pythonPath = Join-Path $backendRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run npm run setup first.' }
$Host.UI.RawUI.WindowTitle = 'SoilSync - private password recovery'
Push-Location $backendRoot
try {
    & $pythonPath scripts/reset_password.py --user-id $UserId
}
finally { Pop-Location }
