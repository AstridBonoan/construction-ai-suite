Param()

Set-StrictMode -Version Latest

Write-Output "Start merge script: $(Get-Date -Format o)"
cd (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)/.. | Out-Null

if (Test-Path ".git\index.lock") { Remove-Item ".git\index.lock" -ErrorAction SilentlyContinue; Write-Output "Removed stale index.lock" }

git fetch origin --prune

$backup = 'backup/main-before-merge-allow-unrelated-2026-01-29'
Write-Output "Creating backup branch $backup from main"
git branch -f $backup main

Write-Output "Checking out main"
git checkout main

Write-Output "Resetting local main to origin/main"
git reset --hard origin/main

Write-Output "Merging origin/feature/project-delay-v5 into main (allow unrelated histories)"
$mergeCmd = 'git merge --no-ff --allow-unrelated-histories origin/feature/project-delay-v5 -m "merge: origin/feature/project-delay-v5 -> main (allow-unrelated-histories)"'
$mergeOut = cmd /c $mergeCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output "Merge failed with exit code $LASTEXITCODE"
    Write-Output $mergeOut
    Write-Output "Attempting to abort merge and restore backup"
    cmd /c "git merge --abort" 2>$null
    cmd /c "git reset --hard $backup" 2>&1 | Write-Output
    Write-Output "Restored main to backup $backup"
    exit 2
} else {
    Write-Output $mergeOut
    Write-Output "Merge succeeded; pushing main to origin"
    cmd /c "git push origin main" 2>&1 | Write-Output
}

Write-Output "Done: $(Get-Date -Format o)"
exit 0
