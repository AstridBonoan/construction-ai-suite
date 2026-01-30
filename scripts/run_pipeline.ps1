param(
    [string]$ImageName = "construction-ai-baseline:latest",
    [string]$Dockerfile = "docker/Dockerfile"
)

Write-Host "Building Docker image $ImageName using $Dockerfile"
docker build -t $ImageName -f $Dockerfile .

Write-Host "Running pipeline inside Docker container (will mount current repo)."
# Recommend mounting user's SSH agent or .git-credentials if needed for pushing.
docker run --rm -v ${PWD}:/workspace -w /workspace $ImageName

Write-Host "Container run complete. Check models/ and analysis_outputs/ for outputs." 
