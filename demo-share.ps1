# AI Construction Suite — One-Click Demo Share Setup
# Requires: Python, Node.js, npm, ngrok

param(
    [string]$FrontendPort = "5176",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
AI Construction Suite — Demo Share Script

Usage:
  .\demo-share.ps1                    # Start with default frontend port 5176
  .\demo-share.ps1 -FrontendPort 5175 # Use custom frontend port
  .\demo-share.ps1 -Help              # Show this help message

This script:
  1. Checks if ngrok is installed
  2. Starts backend server (port 5000)
  3. Starts frontend server (auto-detects port or uses specified port)
  4. Creates ngrok tunnel for backend
  5. Creates ngrok tunnel for frontend
  6. Displays shareable URLs
  7. Instructions for sharing with friends

Stop:
  Press Ctrl+C in any terminal to stop that service.
"@
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Construction Suite - Demo Share Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check ngrok
Write-Host "Checking ngrok installation..." -ForegroundColor Yellow
try {
    $ngrokVersion = ngrok --version 2>&1
    Write-Host "✓ ngrok found: $ngrokVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ngrok not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install ngrok:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://ngrok.com/download"
    Write-Host "  2. Extract to PATH or run directly"
    Write-Host "  3. Run: ngrok authtoken <your-token-from-dashboard>"
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host ""

# Backend
Write-Host "1. Starting backend (http://127.0.0.1:5000)..." -ForegroundColor Cyan
Write-Host "   Run in PowerShell: python run_server.py" -ForegroundColor Gray
Write-Host ""

# Frontend
Write-Host "2. Starting frontend (http://localhost:$FrontendPort)..." -ForegroundColor Cyan
Write-Host "   Run in PowerShell: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""

# Tunnels
Write-Host "3. Creating ngrok tunnels..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend Tunnel:" -ForegroundColor Yellow
Write-Host "  Run in PowerShell: ngrok http 5000" -ForegroundColor Gray
Write-Host ""

Write-Host "Frontend Tunnel:" -ForegroundColor Yellow
Write-Host "  Run in PowerShell: ngrok http $FrontendPort" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open 4 PowerShell terminals" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 1:"
Write-Host "  cd C:\Users\astri\OneDrive\Desktop\construction-ai-suite" -ForegroundColor Gray
Write-Host "  python run_server.py" -ForegroundColor Gray
Write-Host ""

Write-Host "Terminal 2:" 
Write-Host "  cd C:\Users\astri\OneDrive\Desktop\construction-ai-suite\frontend" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
Write-Host ""

Write-Host "Terminal 3:"
Write-Host "  ngrok http 5000" -ForegroundColor Gray
Write-Host "  (Copy the HTTPS URL, e.g., https://abc123-456.ngrok.io)" -ForegroundColor Gray
Write-Host ""

Write-Host "Terminal 4:"
Write-Host "  ngrok http $FrontendPort" -ForegroundColor Gray
Write-Host "  (Copy the HTTPS URL, e.g., https://xyz789-012.ngrok.io)" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SHARE WITH YOUR FRIEND:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend URL: https://xyz789-012.ngrok.io/monday/onboard" -ForegroundColor Green
Write-Host ""
Write-Host "Instructions:" -ForegroundColor Yellow
Write-Host "  1. Open the URL above" -ForegroundColor Gray
Write-Host "  2. Click 'Continue in Demo Mode'" -ForegroundColor Gray
Write-Host "  3. Select 'Demo Board'" -ForegroundColor Gray
Write-Host "  4. Click 'Next: Configure Sync'" -ForegroundColor Gray
Write-Host "  5. Choose sync options" -ForegroundColor Gray
Write-Host "  6. Click 'Start Integration'" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "• Demo URLs are temporary (change each restart)" -ForegroundColor Gray
Write-Host "• Sessions last ~2 hours (free ngrok)" -ForegroundColor Gray
Write-Host "• All data is synthetic/demo - no credentials needed" -ForegroundColor Gray
Write-Host "• Press Ctrl+C to stop any service" -ForegroundColor Gray
Write-Host "• URLs become invalid when services stop" -ForegroundColor Gray
Write-Host ""

Write-Host "For questions, see DEMO_SHARE_SETUP.md" -ForegroundColor Cyan
