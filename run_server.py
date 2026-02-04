#!/usr/bin/env python3
"""
Start the Construction AI Suite backend server
"""
import sys
import os
from pathlib import Path

# Add paths so imports work
project_root = Path(__file__).parent
backend_dir = project_root / "backend"

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "app"))

# Set Flask environment variables
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_DEBUG", "false")

# Import and run the Flask app
os.chdir(str(backend_dir / "app"))
from main import app

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  Construction AI Suite - Backend Server Starting")
    print("="*70)
    print("\n  Server will be available at: http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=5000, debug=False)
