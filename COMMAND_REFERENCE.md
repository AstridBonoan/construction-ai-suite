# Construction AI Suite - Command Reference

Quick commands for deploying and using the system.

## Getting Started

### Windows
```powershell
# Clone repository
git clone https://github.com/yourorg/construction-ai-suite.git
cd construction-ai-suite

# Run system (normal mode)
.\scripts\start.ps1

# Run system (demo mode)
.\scripts\start.ps1 -Demo

# Run system (clean mode - remove logs and cache)
.\scripts\start.ps1 -Clean

# Run validation tests
python scripts/test_fresh_install.py --verbose
```

### macOS/Linux
```bash
# Clone repository
git clone https://github.com/yourorg/construction-ai-suite.git
cd construction-ai-suite

# Make scripts executable
chmod +x scripts/start.sh

# Run system (normal mode)
./scripts/start.sh

# Run system (demo mode)
./scripts/start.sh --demo

# Run system (clean mode)
./scripts/start.sh --clean

# Run validation tests
python scripts/test_fresh_install.py --verbose
```

## Access Points

Once running, the system is available at:

- **Health Check:** `http://localhost:5000/health`
- **Demo Output:** `http://localhost:5000/phase9/outputs`
- **API Base:** `http://localhost:5000/`

## System Control

### View Logs (While Running)

**Windows (PowerShell):**
```powershell
Get-Content -Path "logs\construction_ai.log" -Wait
```

**macOS/Linux:**
```bash
tail -f logs/construction_ai.log
```

### Stop the System
Press `CTRL+C` in the terminal where it's running.

### Restart the System
Just run the startup script again (it handles cleanup).

### Check If Running

**Windows:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/health" | ConvertFrom-Json
```

**macOS/Linux:**
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "ok", "version": "1.0.0", "demo_mode": false}
```

## Configuration

### Using Environment Variables

**Windows (PowerShell):**
```powershell
$env:FLASK_ENV = "production"
$env:DEMO_MODE = "false"
$env:LOG_LEVEL = "INFO"
```

**macOS/Linux:**
```bash
export FLASK_ENV=production
export DEMO_MODE=false
export LOG_LEVEL=INFO
```

### Create .env File

```bash
cp .env.example .env
# Then edit .env with your values
```

## Common Tasks

### Load Your Project Data

**Option 1: CSV File**
```bash
# Place CSV in data/ directory
cp my_projects.csv data/

# CSV must have columns:
# - project_id
# - project_name
# - budget
# - scheduled_duration_days
# - complexity (low/medium/high)
```

**Option 2: API Submission**
```bash
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "P001",
    "project_name": "My Project",
    "budget": 1000000,
    "scheduled_duration_days": 180,
    "complexity": "medium"
  }'
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Get phase 9 outputs (demo mode)
curl http://localhost:5000/phase9/outputs

# Submit project for analysis
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d @project.json
```

### View Application Logs

**Last 50 lines:**
```bash
tail -50 logs/construction_ai.log
```

**Search for errors:**
```bash
grep "ERROR" logs/construction_ai.log
```

**Real-time monitoring:**
```bash
tail -f logs/construction_ai.log
```

## Virtual Environment (Manual)

If you need to manage the virtual environment manually:

### Windows
```powershell
# Activate
.\.venv\Scripts\Activate.ps1

# Deactivate
deactivate

# Install dependencies
pip install -r backend/requirements.txt
```

### macOS/Linux
```bash
# Activate
source .venv/bin/activate

# Deactivate
deactivate

# Install dependencies
pip install -r backend/requirements.txt
```

## Troubleshooting Commands

### Check Python Version
```bash
python --version  # Should be 3.8+
```

### Check if Port 5000 is Available

**Windows:**
```powershell
netstat -ano | findstr :5000
# If in use, kill with: taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -i :5000
# If in use, kill with: kill -9 <PID>
```

### Clear Cache and Logs
```bash
# Windows
.\scripts\start.ps1 -Clean

# macOS/Linux
./scripts/start.sh --clean
```

### Reinstall Dependencies
```bash
pip install -r backend/requirements.txt --force-reinstall
```

### Check Directory Structure
```bash
# Should exist:
# - .venv/
# - backend/app/
# - logs/
# - data/
# - models/
# - config/

ls -la  # macOS/Linux
dir     # Windows
```

## Demo Mode Details

### Run Demo
```bash
# Windows
.\scripts\start.ps1 -Demo

# macOS/Linux
./scripts/start.sh --demo
```

### Demo Projects Included
1. Downtown Office Complex (35% risk)
2. Highway Interchange (72% risk)
3. Residential Housing (22% risk)
4. Water Treatment (72% risk)
5. Parking Lot (18% risk)

### Access Demo Data
```bash
curl http://localhost:5000/phase9/outputs
```

## Production Deployment

### Pre-Deployment Checklist
```bash
# 1. Test fresh install
python scripts/test_fresh_install.py --verbose

# 2. Verify all tests pass
# Should see: "✅ ALL TESTS PASSED - System ready for deployment"

# 3. Setup environment
cp .env.example .env

# 4. Edit .env with production values
# Required for production:
# - FLASK_ENV=production
# - FLASK_DEBUG=false
# - FLASK_SECRET_KEY=<strong-random-key>

# 5. Start system
.\scripts\start.ps1  # Windows
./scripts/start.sh   # macOS/Linux

# 6. Verify health
curl http://localhost:5000/health
```

### Production Environment Variables

```env
# Required
FLASK_ENV=production
FLASK_SECRET_KEY=<generate-strong-random-key>
FLASK_DEBUG=false

# Optional but recommended
LOG_LEVEL=INFO
DEMO_MODE=false

# For databases (if using)
DATABASE_URL=postgresql://user:pass@host/db

# For monitoring
ENABLE_METRICS=true
```

## Development Mode

### Setup for Development
```bash
# Windows
.\scripts\start.ps1

# macOS/Linux
./scripts/start.sh
```

### Run Tests
```bash
# Fresh install test
python scripts/test_fresh_install.py --verbose

# Unit tests (if available)
pytest backend/tests/ -v
```

### Monitor During Development
```bash
# Terminal 1: Run system
./scripts/start.sh

# Terminal 2: Watch logs
tail -f logs/construction_ai.log
```

## Git Operations

### Stage Changes for Commit
```bash
git add .

# Or specific files:
git add UPDATED_README.md PHASE_15_*.md
```

### Commit Changes
```bash
git commit -m "Phase 15: AI Execution Checklist complete"
```

### Push to Remote
```bash
git push origin main
```

### Tag Release
```bash
git tag -a phase15-complete -m "Phase 15 completion"
git push origin phase15-complete
```

## Performance Monitoring

### Check Resource Usage
**Windows (Task Manager):**
```powershell
Get-Process python | Select-Object Name, Handles, @{Name="RAM";Expression={"{0:N0}" -f ($_.WorkingSet64/1mb) + " MB"}}
```

**macOS/Linux:**
```bash
ps aux | grep python
top -p $(pgrep -f "flask run" | head -1)
```

### Monitor API Response Times
```bash
# Simple test
time curl http://localhost:5000/health

# Measure 10 requests
for i in {1..10}; do curl -s http://localhost:5000/health > /dev/null; done
```

## Cleanup and Reset

### Remove Virtual Environment
```bash
rm -rf .venv  # macOS/Linux
rmdir .venv   # Windows
```

### Clear Logs and Cache
```bash
# Windows
.\scripts\start.ps1 -Clean

# macOS/Linux
./scripts/start.sh --clean
```

### Reset Everything
```bash
# WARNING: This removes all local changes
git reset --hard
git clean -fd
```

## Help and Documentation

### Quick Reference
```bash
# View this file
cat COMMAND_REFERENCE.md

# Get help with startup script
./scripts/start.ps1 -Help  # Windows (if implemented)
./scripts/start.sh --help   # macOS/Linux
```

### Full Documentation
- **Setup:** PHASE_15_QUICKSTART.md
- **Usage:** UPDATED_README.md
- **Business:** PHASE_15_BUSINESS.md
- **API:** PHASE_14_INTEGRATION_GUIDE.md
- **Completion:** PHASE_15_COMPLETION_REPORT.md

### Getting Help
1. Check logs: `logs/construction_ai.log`
2. Review Troubleshooting in UPDATED_README.md
3. Run validation: `python scripts/test_fresh_install.py --verbose`
4. Check error messages (usually helpful)

---

## Quick Command Summary

| Task | Windows | macOS/Linux |
|------|---------|-------------|
| **Start normal** | `.\scripts\start.ps1` | `./scripts/start.sh` |
| **Start demo** | `.\scripts\start.ps1 -Demo` | `./scripts/start.sh --demo` |
| **View logs** | `Get-Content logs\construction_ai.log -Wait` | `tail -f logs/construction_ai.log` |
| **Test health** | `Invoke-WebRequest http://localhost:5000/health` | `curl http://localhost:5000/health` |
| **Validate** | `python scripts/test_fresh_install.py` | `python scripts/test_fresh_install.py` |
| **Stop** | `CTRL+C` | `CTRL+C` |
| **Clean** | `.\scripts\start.ps1 -Clean` | `./scripts/start.sh --clean` |

---

**Construction AI Suite - Always Ready to Run** 🚀
