$ErrorActionPreference = "Stop"

Write-Host "[DevPilot] Creating virtual environment..."
py -3.12 -m venv .venv

Write-Host "[DevPilot] Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

Write-Host "[DevPilot] Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "[DevPilot] Installing project in editable mode..."
python -m pip install -e .[dev]

Write-Host "[DevPilot] Running tests..."
pytest -q

Write-Host "[DevPilot] Running readiness check..."
python -m devpilot_core readiness-check
