param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendRoot = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $VenvPython)) {
    throw "Missing virtualenv at .venv. Run: python -m venv .venv; .\.venv\Scripts\pip.exe install -r requirements.txt"
}

if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
    throw "Missing frontend dependencies. Run: cd frontend; npm install"
}

$env:VITE_API_BASE = "http://127.0.0.1:$ApiPort"

Write-Host "Starting API on http://127.0.0.1:$ApiPort"
$ApiProcess = Start-Process `
    -FilePath $VenvPython `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $ProjectRoot `
    -PassThru `
    -WindowStyle Hidden

try {
    Write-Host "Starting frontend on http://127.0.0.1:$FrontendPort"
    Push-Location $FrontendRoot
    npm run dev -- --host 127.0.0.1 --port $FrontendPort
}
finally {
    Pop-Location
    if ($ApiProcess -and -not $ApiProcess.HasExited) {
        Write-Host "Stopping API process $($ApiProcess.Id)"
        Stop-Process -Id $ApiProcess.Id
    }
}
