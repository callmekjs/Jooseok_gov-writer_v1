# run.ps1 — 백엔드(8011) + 프론트(5174) 동시 기동
# 🔴 8010·5173 은 이 PC 의 다른 프로젝트 전용 포트라 여기서 쓰면 안 된다
# (scripts/_common.py 의 FORBIDDEN_PORTS 와 같은 이유). 이 저장소는 8011·5174 를 쓴다.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; .\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --reload --port 8011"
)

if (Test-Path "$root\frontend\package.json") {
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"
    )
}

Write-Host "backend  http://localhost:8011/health"
Write-Host "frontend http://localhost:5174"
