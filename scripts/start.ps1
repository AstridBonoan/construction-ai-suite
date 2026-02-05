# Construction AI Suite - Startup Script for Windows (PowerShell)
#
# Usage: .\scripts\start.ps1 [-Demo] [-Clean]
#
# Options:
#   -Demo   Run in demo mode with sample data
#   -Clean  Remove logs and previous state before starting
#

param (
    [switch]$Demo = $false,
    [switch]$Clean = $false
)

# Colors for output (Windows 10+ supports ANSI)
$Red = "`e[0;31m"
$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Blue = "`e[0;34m"
$NC = "`e[0m"

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "${Blue}════════════════════════════════════════════════════════════════${NC}"
Write-Host "${Blue}   Construction AI Suite - Starting Application${NC}"
Write-Host "${Blue}════════════════════════════════════════════════════════════════${NC}"
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Check Python availability
try {
    $pythonVersion = python --version 2>&1
    Write-Host "${Green}✓ Python found: $pythonVersion${NC}"
} catch {
    Write-Host "${Red}❌ Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "${Yellow}Creating virtual environment...${NC}"
    python -m venv .venv
    Write-Host "${Green}✓ Virtual environment created${NC}"
}

# Activate virtual environment
Write-Host "${Yellow}Activating virtual environment...${NC}"
& .\.venv\Scripts\Activate.ps1
Write-Host "${Green}✓ Virtual environment activated${NC}"

# Install/update dependencies
Write-Host "${Yellow}Installing dependencies...${NC}"
pip install -q -r backend/requirements.txt 2>$null
Write-Host "${Green}✓ Dependencies installed${NC}"

# Create required directories
Write-Host "${Yellow}Setting up directories...${NC}"
@("logs", "models", "data", "config") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}
Write-Host "${Green}✓ Directories ready${NC}"

# Setup environment
if (-not (Test-Path ".env")) {
    Write-Host "${Yellow}Creating .env from .env.example...${NC}"
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        # Set DEMO_MODE if requested
        if ($Demo) {
            (Get-Content ".env") -replace "^DEMO_MODE=false", "DEMO_MODE=true" | Set-Content ".env"
            Write-Host "${Green}✓ Demo mode enabled in .env${NC}"
        }
    } else {
        Write-Host "${Yellow}⚠ .env.example not found - using defaults${NC}"
    }
}

# Load environment from .env file
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -and -not $_.StartsWith("#") } | ForEach-Object {
        $name, $value = $_ -split "=", 2
        if ($name -and $value) {
            $name = $name.Trim()
            $value = $value.Trim()
            Set-Item -Path "env:$name" -Value $value -ErrorAction SilentlyContinue
        }
    }
}

# Clean mode
if ($Clean) {
    Write-Host "${Yellow}Cleaning logs and cache...${NC}"
    @("logs", "__pycache__", ".pytest_cache") | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "${Green}✓ Cache cleaned${NC}"
}

# Verify Phase 14 is integrated
Write-Host "${Yellow}Verifying Phase 14 integration...${NC}"
$phase14Check = python -c "from backend.app.phase14_logging import setup_logging; from backend.app.phase14_errors import safe_api_call; print('OK')" 2>$null
if ($phase14Check -eq "OK") {
    Write-Host "${Green}✓ Phase 14 modules available${NC}"
} else {
    Write-Host "${Yellow}⚠ Phase 14 not integrated yet (optional for demo)${NC}"
}

# Display startup info
Write-Host "${Blue}════════════════════════════════════════════════════════════════${NC}"
Write-Host "${Green}Starting Construction AI Suite...${NC}"
Write-Host ""
Write-Host "${Yellow}Application Configuration:${NC}"
Write-Host "  Environment: $(if ($env:FLASK_ENV) { $env:FLASK_ENV } else { "development" })"
Write-Host "  Debug Mode: $(if ($env:FLASK_DEBUG) { $env:FLASK_DEBUG } else { "false" })"
Write-Host "  Log Level: $(if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { "INFO" })"
Write-Host "  Demo Mode: $Demo"
Write-Host ""
Write-Host "${Yellow}Access Points:${NC}"
Write-Host "  Backend API: http://localhost:5000"
Write-Host "  Health Check: http://localhost:5000/health"
Write-Host "  Phase 9 Outputs: http://localhost:5000/phase9/outputs"
Write-Host ""
Write-Host "${Yellow}Logs:${NC}"
Write-Host "  Location: $(Get-Location)/logs/"
Write-Host "  View: Get-Content logs/construction_ai.log -Tail 20 -Wait"
Write-Host ""
Write-Host "${Yellow}To stop the server, press Ctrl+C${NC}"
Write-Host "${Blue}════════════════════════════════════════════════════════════════${NC}"
Write-Host ""

# Set environment variables for Flask
$env:PYTHONUNBUFFERED = "1"
$env:FLASK_APP = "app/main.py"

if ($Demo) {
    $env:DEMO_MODE = "true"
    Write-Host "${Green}🎬 Running in DEMO MODE${NC}"
}

# Change to backend directory
Set-Location "backend"

# Run the application
python -m flask run --host=0.0.0.0 --port=5000
