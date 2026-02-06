$env:GIT_PAGER = "cat"
git push origin main 2>&1 | Out-String
