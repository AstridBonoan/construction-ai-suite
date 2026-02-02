# Sync all local branches to origin non-interactively
# - create backups for branches that would be reset
# - push branches that are only ahead
# - reset local branches to origin when behind or diverged (backup preserved)
# - attempt merge of origin/feature/project-delay-v5 into main and push if successful

param()

Set-StrictMode -Version Latest
$date = Get-Date -Format "yyyy-MM-dd_HH-mm"
$repo = Get-Location
Write-Output "Running branch sync at $date in $repo"

# remove stale lock if present
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -ErrorAction SilentlyContinue
    Write-Output "Removed stale .git/index.lock"
}

# fetch all
git fetch --all --prune

$branchesRaw = git for-each-ref --format='%(refname:short)' refs/heads
$branches = $branchesRaw -split "\r?\n" | Where-Object { $_ -ne '' }

$summary = @{
    timestamp = $date
    processed = @()
    push_attempts = @()
    reset_backups = @()
    errors = @()
}

foreach ($b in $branches) {
    Write-Output "\n=== Processing branch: $b ==="
    try {
        $originRef = git rev-parse --verify origin/$b 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Output "No origin/$b exists -> pushing branch to origin"
            git push --set-upstream origin $b 2>&1 | Write-Output
            $summary.push_attempts += $b
            continue
        }
        $counts = git rev-list --left-right --count origin/$b...$b 2>$null
        if (-not $counts) { Write-Output "Could not compute divergence for $b"; continue }
        $parts = $counts -split "\s+"
        if ($parts.Length -lt 2) { Write-Output "Unexpected rev-list output: $counts"; continue }
        $behind = [int]$parts[0]
        $ahead  = [int]$parts[1]
        Write-Output "ahead=$ahead, behind=$behind"
        if ($behind -eq 0 -and $ahead -eq 0) {
            Write-Output "$b is up-to-date with origin/$b"
        } elseif ($behind -eq 0 -and $ahead -gt 0) {
            Write-Output "$b is ahead only -> pushing to origin"
            git push --set-upstream origin $b 2>&1 | Write-Output
            $summary.push_attempts += $b
        } else {
            Write-Output "$b is behind or diverged -> backing up and resetting to origin/$b"
            $backup = "backup/$b-before-sync-$date"
            git branch -f $backup $b 2>&1 | Write-Output
            $summary.reset_backups += @{ branch = $b; backup = $backup }
            git checkout $b 2>&1 | Write-Output
            git reset --hard origin/$b 2>&1 | Write-Output
            git branch --set-upstream-to=origin/$b $b 2>&1 | Write-Output
        }
        $summary.processed += $b
    } catch {
        $err = $_ | Out-String
        Write-Output ("Error processing {0}: {1}" -f $b, $err)
        $summary.errors += @{ branch = $b; error = $err }
    }
}

# Attempt merge into main using origin/feature/project-delay-v5 as source
Write-Output "\n=== Merge feature/project-delay-v5 into main (using origin/feature/project-delay-v5) ==="
try {
    # ensure main matches origin/main
    git fetch origin main 2>&1 | Write-Output
    git checkout main 2>&1 | Write-Output
    git reset --hard origin/main 2>&1 | Write-Output

    # perform merge
    $mergeOutput = git merge --no-ff origin/feature/project-delay-v5 -m "merge: origin/feature/project-delay-v5 -> main (chore/v8 expanded RuleB)" 2>&1
    Write-Output $mergeOutput
    if ($LASTEXITCODE -ne 0) {
        Write-Output "Merge returned non-zero exit code. Aborting and recording status."
        git merge --abort 2>&1 | Write-Output
        $summary.errors += @{ merge = 'merge_failed'; output = ($mergeOutput -join "`n") }
    } else {
        Write-Output "Merge succeeded. Pushing main to origin."
        git push origin main 2>&1 | Write-Output
        $summary.merged_main = @{ merged = $true; source = 'origin/feature/project-delay-v5' }
    }
} catch {
    Write-Output "Merge step error: $_"
    $summary.errors += @{ merge = 'exception'; error = $_.ToString() }
}

# write summary file
$summaryPath = "data_splits/v8/sync_summary_$date.json"
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryPath -Encoding utf8
Write-Output "Wrote summary to $summaryPath"

Write-Output "\nDone. Review $summaryPath for details. Backups are under refs/heads/backup/* if you need to restore any local work."

Exit 0
