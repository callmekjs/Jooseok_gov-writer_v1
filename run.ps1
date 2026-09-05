# run.ps1 — 백엔드(8010) + 프론트(5173) 동시 기동
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; .\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --reload --port 8010"
)

if (Test-Path "$root\frontend\package.json") {
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"
    )
}

Write-Host "backend  http://localhost:8010/health"
Write-Host "frontend http://localhost:5173"
