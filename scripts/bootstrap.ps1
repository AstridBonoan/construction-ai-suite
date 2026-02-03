# Bootstrap script for Windows PowerShell: installs git hooks and optionally pre-commit
Param()
Set-StrictMode -Version Latest
$python = 'python'
if (Test-Path '.\venv\Scripts\python.exe') {
    $python = '.\venv\Scripts\python.exe'
}

Write-Host "Running installer: $python scripts/install_hooks.py"
& $python scripts/install_hooks.py

try {
    if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
        Write-Host 'pre-commit found; installing pre-commit hooks'
        pre-commit install
    } else {
        Write-Host 'pre-commit not found. To enable managed hooks, run: pip install pre-commit; pre-commit install'
    }
} catch {
    Write-Warning "Failed to run pre-commit install: $_"
}

Write-Host 'Bootstrap complete.'
