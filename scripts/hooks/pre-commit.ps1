# Repository hook template (PowerShell): run scripts/ci_checks.py and block commit if it fails
$python = 'python'
if (Test-Path '.venv\Scripts\python.exe') {
    $python = '.\venv\Scripts\python.exe'
}
Write-Host 'Running CI checks (scripts/ci_checks.py)...'
& $python scripts/ci_checks.py
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Pre-commit: CI checks failed. Commit aborted.'
    exit $LASTEXITCODE
}
exit 0
