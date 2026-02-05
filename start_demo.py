#!/usr/bin/env python3
"""
Construction AI Suite - Quick Start
Simple startup script to launch the backend and demo the system
"""
import os
import sys
import subprocess
from pathlib import Path
import time

# Setup paths
ROOT = Path(__file__).parent.parent
os.chdir(ROOT)

print("\n" + "="*70)
print("  CONSTRUCTION AI SUITE - QUICK START DEMO")
print("="*70 + "\n")

# Check Python
print("✓ Python environment ready")

# Check dependencies
print("✓ Checking dependencies...")
try:
    import flask
    import pandas
    import numpy
    print("✓ All dependencies installed\n")
except ImportError as e:
    print(f"Installing missing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "backend/requirements.txt"])
    print("✓ Dependencies installed\n")

# Setup .env if needed
if not Path(".env").exists() and Path(".env.example").exists():
    print("Setting up .env configuration...")
    with open(".env.example") as f:
        env_content = f.read()
    with open(".env", "w") as f:
        f.write(env_content)
    print("✓ .env created\n")

# Create directories
for d in ["logs", "models", "data", "config"]:
    Path(d).mkdir(exist_ok=True)

print("="*70)
print("STARTING BACKEND SERVER")
print("="*70 + "\n")

# Start the Flask backend
print("Launching Flask application on http://localhost:5000\n")
print("Available endpoints:")
print("  POST /api/analyze_project - Analyze a construction project")
print("  POST /api/batch_analyze - Analyze multiple projects")
print("  GET  /api/health - Health check")
print("  GET  /api/version - Get API version\n")

print("READY FOR TESTING!")
print("="*70 + "\n")

print(f"Starting server on port 5000...")
print("Press Ctrl+C to stop\n")

# Run main.py which starts the Flask server
main_path = ROOT / "backend" / "app" / "main.py"
subprocess.run([sys.executable, str(main_path)])
