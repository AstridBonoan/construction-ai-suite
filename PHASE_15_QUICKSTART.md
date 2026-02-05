# Phase 15: Quick Start Guide

**Construction AI Suite - Get Running in 5 Minutes**

---

## Prerequisites (Check First)

- ✅ Git installed (for cloning repo)
- ✅ Python 3.8 or newer (check: `python --version`)
- ✅ 500MB disk space available
- ✅ Internet access (first run only, for pip dependencies)

**Don't have Python?**
- Windows: Download from [python.org](https://www.python.org/downloads/) (check "Add Python to PATH")
- macOS: `brew install python3`
- Linux: `sudo apt install python3` (Debian/Ubuntu) or `sudo yum install python3` (RHEL/CentOS)

---

## 5-Minute Setup

### Step 1: Clone Repository (1 minute)

**Windows (Command Prompt or PowerShell):**
```powershell
git clone https://github.com/yourorg/construction-ai-suite.git
cd construction-ai-suite
```

**macOS/Linux (Terminal):**
```bash
git clone https://github.com/yourorg/construction-ai-suite.git
cd construction-ai-suite
```

### Step 2: Run Startup Script (3 minutes)

**Windows (PowerShell):**
```powershell
.\scripts\start.ps1
```

**macOS/Linux (Terminal):**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

The script will:
- ✅ Create Python virtual environment (`.venv`)
- ✅ Install dependencies (`pip install -r backend/requirements.txt`)
- ✅ Create required directories (logs, models, data)
- ✅ Setup environment configuration (`.env`)
- ✅ Start the Flask server

**Output should look like:**
```
======================================================================
  Construction AI Suite - Initialization
======================================================================
  Environment: development
  Debug Mode: false
  Demo Mode: false
  Log Level: INFO
  Phase 14: ✓ Production Hardening Available
  
  Endpoints:
    • Health Check: http://localhost:5000/health
    • Phase 9 Outputs: http://localhost:5000/phase9/outputs
  
  Logs: /path/to/logs/construction_ai.log
======================================================================

Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Step 3: Test It (1 minute)

Open your browser and visit:
```
http://localhost:5000/health
```

You should see:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "demo_mode": false
}
```

**Success!** System is running.

---

## Try Demo Mode (Get Sample Data)

Want to see it work without your own data?

### Windows:
```powershell
.\scripts\start.ps1 -Demo
```

### macOS/Linux:
```bash
./scripts/start.sh --demo
```

Startup message will show:
```
  Demo Mode: true
```

Then visit:
```
http://localhost:5000/phase9/outputs
```

You'll see 5 sample projects with:
- **Risk scores** (18% to 72%)
- **Predicted delays** (1 to 25 days)
- **Recommendations** (plain English)
- **Confidence levels** (70-85%)

---

## Common Tasks

### View Logs (See What System is Doing)

**While system is running:**
```bash
# macOS/Linux
tail -f logs/construction_ai.log

# Windows (in new PowerShell window)
Get-Content -Path "logs\construction_ai.log" -Wait
```

### Stop the System

Press `CTRL+C` in the terminal where it's running.

### Restart After Stopping

```powershell
# Windows
.\scripts\start.ps1

# macOS/Linux
./scripts/start.sh
```

### Clean Up (Remove Logs & Cache)

**Windows:**
```powershell
.\scripts\start.ps1 -Clean
```

**macOS/Linux:**
```bash
./scripts/start.sh --clean
```

This removes:
- Old logs
- Model cache
- Temporary files

But keeps your data and configuration.

---

## Load Your Own Data

### Step 1: Prepare CSV File

Create a file like `data/my_projects.csv`:

```csv
project_id,project_name,budget,scheduled_duration_days,complexity,team_size
P001,Downtown Office,$2500000,180,medium,45
P002,Highway Interchange,$50000000,365,high,120
P003,Residential Complex,$8500000,270,medium,60
```

**Required columns:**
- `project_id` - Unique identifier
- `project_name` - Human readable name
- `budget` - Project cost in dollars
- `scheduled_duration_days` - Timeline in days
- `complexity` - low, medium, or high

**Optional columns:**
- `team_size` - Number of team members
- `location` - Geographic location
- `status` - active, completed, paused
- `risk_factors` - Comma-separated risk items
- `actual_spend` - If project is complete
- `actual_duration_days` - If project is complete

### Step 2: Place File in Data Directory

Move your CSV to:
```
construction-ai-suite/data/my_projects.csv
```

### Step 3: Submit to API

**Using curl (Command Line):**

```bash
# Read file and submit
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "P001",
    "project_name": "Downtown Office",
    "budget": 2500000,
    "scheduled_duration_days": 180,
    "complexity": "medium",
    "team_size": 45
  }'
```

**Response:**
```json
{
  "risk_score": 0.35,
  "delay_probability": 0.28,
  "predicted_delay_days": 5,
  "confidence": 0.85,
  "explanation": {
    "summary": "Low Risk. Standard planning sufficient.",
    "factors": [
      "Similar projects averaged 5-day delays",
      "Team size is adequate for scope"
    ],
    "recommendations": [
      "Standard contingency planning (5-10%)",
      "Monthly progress reviews",
      "Standard quality inspections"
    ]
  }
}
```

### Step 4: Integrate Into Your Workflow

**Option A: Manual Analysis**
1. Export project list to CSV
2. Submit to API
3. Review recommendations in Excel
4. Share with team

**Option B: Automated Reporting**
1. Write Python script to read local DB
2. Submit projects to API on schedule
3. Log results and track predictions
4. Auto-generate reports for management

**Option C: Web Dashboard (Optional)**
- Use `/phase9/outputs` endpoint
- Build custom UI with results
- Integrate with project management tool

---

## Understanding the Output

### What Is Risk Score?

A percentage (0-100%) of how likely the project is to have issues:

```
0-30%   = LOW RISK      (Green)   - Standard planning OK
30-60%  = MEDIUM RISK   (Yellow)  - Closer monitoring needed
60-100% = HIGH RISK     (Red)     - Special attention required
```

**Example interpretations:**
- **18% risk:** "This is a straightforward project"
- **35% risk:** "Some complexity, need solid planning"
- **72% risk:** "This project has significant challenges ahead"

### What Is Delay Prediction?

How many days the project is **likely to slip** based on history:

```
0-5 days     = Small variance (normal)
5-15 days    = Significant delay (concerning)
15+ days     = Major delay (critical attention)
```

**Example:**
- Score 35%, Prediction +5 days = "Might slip one week, plan accordingly"
- Score 72%, Prediction +18 days = "Expect 3-week delay without intervention"

### What Is Confidence?

How sure the system is about its prediction (75-90%):

```
75% confidence = "This prediction is probably right, but could miss"
85% confidence = "Pretty sure about this, reasonable to rely on"
90% confidence = "Very confident in this assessment"
```

**What to do with confidence:**
- High confidence → Act decisively on recommendation
- Lower confidence → Monitor more closely, test assumptions

### What Are Recommendations?

Actions to keep project on track:

```
Examples:
- "Add 10-15% time buffer to schedule"
- "Pre-order long-lead materials immediately"
- "Increase site supervision to weekly"
- "Cross-train backup team members"
- "Establish daily risk standups"
```

These are **suggestions** based on similar past projects. Your team's judgment still matters.

---

## Interpreting Sample Projects

If you're running demo mode, here's what the 5 samples mean:

### Sample 1: Downtown Office Complex (35% Risk)

```json
{
  "project_name": "Downtown Office Complex",
  "risk_score": 0.35,
  "delay_probability": 0.28,
  "predicted_delay_days": 5,
  "budget": "$2.5M",
  "complexity": "medium"
}
```

**Interpretation:** 
- Fairly straightforward project
- About 1 in 4 chance of 5-day delay
- Standard project management OK
- No special risk mitigation needed

**What this looks like in practice:**
```
Plan for: 6 months
Likely outcome: 6 months 1 week
Why: Team coordination, normal material delays
Action: Standard contingency planning (5-10%)
```

### Sample 2: Highway Interchange (72% Risk)

```json
{
  "project_name": "Highway Interchange Expansion",
  "risk_score": 0.72,
  "delay_probability": 0.81,
  "predicted_delay_days": 18,
  "budget": "$50M",
  "complexity": "high"
}
```

**Interpretation:**
- Complex project with real challenges
- 4 in 5 chance of 18-day slip
- Significant risk management needed
- Proactive approach required

**What this looks like in practice:**
```
Plan for: 12 months
Likely outcome: 12.5 months (18 days)
Why: Regulatory coordination, weather, scope complexity
Action: Add 20-30% contingency, weekly risk reviews, escalation procedures
```

---

## Next Steps

### For Casual Testing
1. ✅ Run demo mode
2. ✅ See how outputs look
3. ✅ Understand risk concepts
4. ✅ Share with team for feedback

### For Pilot Program
1. ✅ Prepare 5-10 recent completed projects
2. ✅ Submit to system
3. ✅ Compare predictions vs. actual outcomes
4. ✅ Refine understanding of risk factors
5. → Start using on current projects

### For Production Deployment
1. ✅ Prepare all historical project data (ideally 50+)
2. ✅ Setup `.env` file with production config
3. ✅ Integrate API into project tools
4. ✅ Train team on using recommendations
5. ✅ Establish escalation procedures
6. → Monitor and improve monthly

---

## Troubleshooting

### Problem: "Python not found"

**Windows:**
1. Open Command Prompt
2. Type: `python --version`
3. If not found, install from [python.org](https://www.python.org)
4. Make sure "Add Python to PATH" is checked
5. Restart terminal

**macOS:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt install python3  # Debian/Ubuntu
sudo yum install python3  # RHEL/CentOS
```

### Problem: "Port 5000 is already in use"

Another application is using port 5000:

**Windows (Find and kill the process):**
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -i :5000
kill -9 <PID>
```

Or change port in `.env`:
```
FLASK_PORT=5001
```

### Problem: Module import errors

Try reinstalling dependencies:

```bash
# Windows
.\scripts\start.ps1

# macOS/Linux
./scripts/start.sh
```

If still failing:
```bash
pip install -r backend/requirements.txt --force-reinstall
```

### Problem: No results from API

**Check 1:** Is system running?
```bash
curl http://localhost:5000/health
```

**Check 2:** Is demo mode enabled?
```
# In .env file
DEMO_MODE=true
```

**Check 3:** Is your data format correct?
```json
{
  "project_id": "P001",
  "project_name": "My Project",
  "budget": 1000000,
  "scheduled_duration_days": 180
}
```

**Check 3:** Check logs
```bash
# View latest 50 lines
tail -50 logs/construction_ai.log
```

### Problem: System crashed with error

**Get the error details:**

**Windows:**
```powershell
Get-Content -Path "logs\construction_ai.log" -Tail 100
```

**macOS/Linux:**
```bash
tail -100 logs/construction_ai.log
```

Look for the error message, then:
1. Check [UPDATED_README.md](UPDATED_README.md) Troubleshooting
2. Verify all prerequisites installed
3. Try clean restart: `./scripts/start.sh --clean`

---

## Getting Help

| Question | Answer Location |
|----------|-----------------|
| How does this work? | [UPDATED_README.md](UPDATED_README.md) - How It Works section |
| What's the business case? | [PHASE_15_BUSINESS.md](PHASE_15_BUSINESS.md) |
| Technical details? | [PHASE_14_INTEGRATION_GUIDE.md](PHASE_14_INTEGRATION_GUIDE.md) |
| Something broken? | Troubleshooting above, or check logs/ folder |
| Terminology? | [UPDATED_README.md](UPDATED_README.md) - Glossary |

---

## Video Walkthrough (Optional)

If available, watch the 5-minute demo:
- Part 1: Setup (2 min)
- Part 2: Demo mode results (1 min)
- Part 3: Loading your data (1 min)
- Part 4: Using recommendations (1 min)

---

## What to Do Next

### Immediate (Today)
- ✅ Get system running
- ✅ Try demo mode
- ✅ Look at sample outputs
- ✅ Show team demo

### This Week
- ✅ Prepare 5 recent completed projects
- ✅ Submit to system
- ✅ Compare predictions vs. actual
- ✅ Gather team feedback

### This Month
- ✅ Document any insights
- ✅ Identify quick wins
- ✅ Plan pilot with current projects
- ✅ Schedule full integration

---

## Success Looks Like

**Week 1:** "System works, outputs make sense"
**Week 2:** "Predictions look reasonable vs. our experience"  
**Week 3:** "Team sees value in recommendations"
**Month 1:** "Using AI insights in project meetings"
**Month 3:** "Measurable improvement in on-time delivery"
**Month 6:** "AI is standard part of project governance"

---

## Summary

| What | How | Time |
|------|-----|------|
| Install | `./scripts/start.ps1` | 3 min |
| Try demo | Add `-Demo` flag | 2 min |
| Test it | Visit `localhost:5000/health` | 1 min |
| Load data | CSV in `data/` folder | 5 min |
| Use results | Read recommendations | ongoing |

**Total to working system: 5 minutes**

Get started now and see what your projects look like through an AI lens.

---

**Questions?** See Troubleshooting above or check the full [README](UPDATED_README.md).
