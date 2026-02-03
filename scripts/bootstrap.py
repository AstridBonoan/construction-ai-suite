"""
Cross-platform bootstrapper.

Runs the appropriate platform bootstrap script (`scripts/bootstrap.sh` or
`scripts/bootstrap.ps1`) and optionally installs `pre-commit` if the user agrees.

This script is idempotent and relies on `scripts/install_hooks.py` to perform
safe hook installs (backs up differing hooks, skips identical ones).
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "scripts" / "bootstrap.sh"
PS1 = ROOT / "scripts" / "bootstrap.ps1"


def run_cmd(cmd, shell=False):
    print(f"Running: {' '.join(cmd) if isinstance(cmd, (list,tuple)) else cmd}")
    res = subprocess.run(cmd, shell=shell)
    return res.returncode


def prompt_yesno(prompt, default=True):
    yn = "Y/n" if default else "y/N"
    resp = input(f"{prompt} [{yn}]: ").strip().lower()
    if resp == "":
        return default
    return resp in ("y", "yes")


def main():
    system = platform.system()
    print(f"Detected OS: {system}")

    # Prefer running platform-specific bootstrap script if present
    if system == "Windows" and PS1.exists():
        print(f"Using PowerShell bootstrap: {PS1}")
        # Run PowerShell script
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PS1),
        ]
        rc = run_cmd(cmd)
        if rc != 0:
            print("PowerShell bootstrap returned non-zero exit code")
    elif SH.exists():
        print(f"Using shell bootstrap: {SH}")
        # Run with sh to ensure POSIX behavior
        cmd = ["sh", str(SH)]
        rc = run_cmd(cmd)
        if rc != 0:
            print("Shell bootstrap returned non-zero exit code")
    else:
        # Fallback: call installer directly
        print("No platform bootstrap script found; running installer directly")
        rc = run_cmd([sys.executable, str(ROOT / "scripts" / "install_hooks.py")])

    # Prompt to optionally install pre-commit for managed hooks
    if prompt_yesno("Install and enable pre-commit (recommended)?"):
        print("Installing pre-commit (pip install pre-commit) and enabling hooks")
        rc_install = run_cmd([sys.executable, "-m", "pip", "install", "pre-commit"])
        if rc_install == 0:
            run_cmd(["pre-commit", "install"])
        else:
            print("Failed to install pre-commit via pip; you can install it manually")

    print("Bootstrap finished.")


if __name__ == "__main__":
    main()
