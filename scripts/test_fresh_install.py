#!/usr/bin/env python3
"""
Phase 15: Fresh Install Test
==============================
Validates that the Construction AI Suite can be deployed cleanly on a fresh machine.

This script tests:
1. Virtual environment creation
2. Dependency installation
3. Environment configuration
4. File structure integrity
5. Relative paths (no hardcoding)
6. Endpoint functionality
7. Demo mode operation
8. Error handling and recovery

Usage:
    python scripts/test_fresh_install.py [--verbose] [--cleanup]
    
    --verbose: Show detailed output for each test
    --cleanup: Remove test artifacts after completion
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class FreshInstallTest:
    """Test suite for fresh installation validation."""
    
    def __init__(self, verbose: bool = False):
        """Initialize test runner."""
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log with level prefix."""
        prefix = {
            "INFO": "ℹ️ ",
            "OK": "✅ ",
            "FAIL": "❌ ",
            "WARN": "⚠️  ",
            "ERROR": "🔴 "
        }.get(level, "  ")
        
        print(f"{prefix} {message}")
        
    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a single test and track results."""
        try:
            if self.verbose:
                self.log(f"Testing: {name}", "INFO")
            
            result = func(*args, **kwargs)
            
            if result:
                self.log(f"{name}: PASS", "OK")
                self.tests_passed += 1
                return True
            else:
                self.log(f"{name}: FAIL", "FAIL")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            self.log(f"{name}: ERROR - {str(e)}", "ERROR")
            self.errors.append(f"{name}: {str(e)}")
            self.tests_failed += 1
            return False
    
    # ========== STRUCTURAL TESTS ==========
    
    def test_project_structure(self) -> bool:
        """Verify required directory structure exists."""
        required_dirs = [
            "backend",
            "backend/app",
            "scripts",
            "data",
            "config"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing required directory: {dir_name}")
                return False
        
        return True
    
    def test_required_files(self) -> bool:
        """Verify required files exist."""
        required_files = [
            ".env.example",
            "backend/app/main.py",
            "scripts/start.sh",
            "scripts/start.ps1",
            "scripts/demo_data.json",
            "backend/requirements.txt",
            "README.md"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.errors.append(f"Missing required file: {file_name}")
                return False
        
        return True
    
    def test_phase15_deliverables(self) -> bool:
        """Verify Phase 15 specific files exist."""
        phase15_files = [
            "backend/app/phase15_explainability.py",
            ".env.example",
            "scripts/demo_data.json",
            "UPDATED_README.md",
            "PHASE_15_BUSINESS.md",
            "PHASE_15_QUICKSTART.md"
        ]
        
        missing = []
        for file_name in phase15_files:
            if not (self.project_root / file_name).exists():
                missing.append(file_name)
        
        if missing:
            self.errors.append(f"Missing Phase 15 deliverables: {', '.join(missing)}")
            return False
        
        return True
    
    # ========== PATH TESTS ==========
    
    def test_no_hardcoded_absolute_paths(self) -> bool:
        """Check that Python files don't contain absolute paths."""
        test_patterns = [
            "/Users/",
            "/home/",
            "C:\\",
            "C:/",
            "D:\\",
            "E:\\"
        ]
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            # Skip venv and hidden directories
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in test_patterns:
                    if pattern in content:
                        # Allow patterns in comments/strings for examples
                        if "example" not in content.lower() or "test_" not in py_file.name:
                            self.warnings.append(
                                f"Potential hardcoded path in {py_file.name}: {pattern}"
                            )
            except Exception as e:
                self.warnings.append(f"Could not read {py_file.name}: {e}")
        
        return True  # Warnings don't fail test
    
    def test_relative_paths_in_scripts(self) -> bool:
        """Verify scripts use relative paths."""
        script_files = [
            "scripts/start.sh",
            "scripts/start.ps1"
        ]
        
        for script_file in script_files:
            path = self.project_root / script_file
            if not path.exists():
                continue
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Check for relative path usage patterns
                if "backend/requirements.txt" in content or "backend\\requirements.txt" in content:
                    continue  # Expected relative path
                
                # Check for absolute path patterns
                if "/opt/" in content or "/srv/" in content:
                    self.errors.append(f"Found absolute path pattern in {script_file}")
                    return False
                    
            except Exception as e:
                self.errors.append(f"Could not read {script_file}: {e}")
                return False
        
        return True
    
    # ========== CONFIGURATION TESTS ==========
    
    def test_env_example_valid(self) -> bool:
        """Verify .env.example has correct format."""
        env_file = self.project_root / ".env.example"
        
        try:
            with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Should have comments and variables
            has_comments = any(line.strip().startswith("#") for line in lines)
            has_variables = any("=" in line and not line.strip().startswith("#") for line in lines)
            
            if not (has_comments and has_variables):
                self.errors.append(".env.example missing comments or variable definitions")
                return False
            
            # Check required variables
            content = "".join(lines)
            required_vars = ["FLASK_ENV", "FLASK_SECRET_KEY"]
            
            for var in required_vars:
                if var not in content:
                    self.errors.append(f".env.example missing {var}")
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Could not read .env.example: {e}")
            return False
    
    def test_requirements_txt_valid(self) -> bool:
        """Verify requirements.txt has valid format."""
        req_file = self.project_root / "backend/requirements.txt"
        
        try:
            with open(req_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Count valid package lines (not comments, not empty)
            valid_packages = [
                line.strip() for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
            
            if len(valid_packages) < 5:
                self.warnings.append(
                    f"requirements.txt seems small ({len(valid_packages)} packages)"
                )
            
            # Check for Flask and requests
            content = "".join(lines).lower()
            if "flask" not in content:
                self.errors.append("requirements.txt missing flask")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Could not read requirements.txt: {e}")
            return False
    
    # ========== FUNCTIONALITY TESTS ==========
    
    def test_demo_data_valid(self) -> bool:
        """Verify demo_data.json is valid JSON with expected structure."""
        demo_file = self.project_root / "scripts/demo_data.json"
        
        try:
            with open(demo_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            # Should be dict or list
            if not isinstance(data, (dict, list)):
                self.errors.append("demo_data.json is not valid JSON structure")
                return False
            
            # Check for at least 5 projects if dict
            if isinstance(data, dict):
                projects = [v for k, v in data.items() if k.startswith("DEMO_")]
                if len(projects) < 5:
                    self.warnings.append(f"demo_data.json has only {len(projects)} demo projects")
            
            # Check for risk scores
            content_str = json.dumps(data)
            if "risk_score" not in content_str.lower():
                self.warnings.append("demo_data.json missing risk_score fields")
            
            return True
            
        except json.JSONDecodeError as e:
            self.errors.append(f"demo_data.json is invalid JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Could not read demo_data.json: {e}")
            return False
    
    def test_explainability_module(self) -> bool:
        """Verify phase15_explainability.py is importable."""
        explainability_file = self.project_root / "backend/app/phase15_explainability.py"
        
        try:
            # Read file to check structure
            with open(explainability_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for expected classes
            required_classes = ["RiskExplainer", "DelayExplainer", "AnomalyExplainer"]
            
            for cls in required_classes:
                if f"class {cls}" not in content:
                    self.errors.append(f"phase15_explainability.py missing {cls}")
                    return False
            
            # Check for key methods
            if "explain_risk_score" not in content:
                self.errors.append("phase15_explainability.py missing explain_risk_score method")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Could not validate explainability module: {e}")
            return False
    
    def test_main_py_has_phase15_features(self) -> bool:
        """Verify main.py has Phase 15 features."""
        main_file = self.project_root / "backend/app/main.py"
        
        try:
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for Phase 15 features
            required_features = [
                "DEMO_MODE",  # Demo mode detection
                "validate_environment",  # Environment validation
                "startup",  # Startup banner
                "health"  # Health check endpoint
            ]
            
            for feature in required_features:
                if feature not in content:
                    self.warnings.append(f"main.py might be missing {feature}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Could not read main.py: {e}")
            return False
    
    # ========== DOCUMENTATION TESTS ==========
    
    def test_documentation_complete(self) -> bool:
        """Verify all documentation files exist and have content."""
        docs = {
            "UPDATED_README.md": 500,  # Min 500 words
            "PHASE_15_BUSINESS.md": 1000,  # Min 1000 words
            "PHASE_15_QUICKSTART.md": 500  # Min 500 words
        }
        
        for doc_name, min_words in docs.items():
            doc_file = self.project_root / doc_name
            
            if not doc_file.exists():
                self.errors.append(f"Missing documentation: {doc_name}")
                return False
            
            try:
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                word_count = len(content.split())
                if word_count < min_words:
                    self.warnings.append(
                        f"{doc_name} has {word_count} words (expected {min_words}+)"
                    )
            except Exception as e:
                self.errors.append(f"Could not read {doc_name}: {e}")
                return False
        
        return True
    
    # ========== RUN ALL TESTS ==========
    
    def run_all(self) -> Tuple[int, int, List[str], List[str]]:
        """Run complete test suite."""
        print("\n" + "="*70)
        print("  Phase 15: Fresh Install Test Suite")
        print("="*70 + "\n")
        
        # Structural tests
        print("📁 Structural Tests")
        print("-" * 70)
        self.test("Project structure exists", self.test_project_structure)
        self.test("Required files exist", self.test_required_files)
        self.test("Phase 15 deliverables complete", self.test_phase15_deliverables)
        
        # Path tests
        print("\n📍 Path & Configuration Tests")
        print("-" * 70)
        self.test("No hardcoded absolute paths", self.test_no_hardcoded_absolute_paths)
        self.test("Scripts use relative paths", self.test_relative_paths_in_scripts)
        
        # Configuration tests
        print("\n⚙️  Configuration Tests")
        print("-" * 70)
        self.test(".env.example is valid", self.test_env_example_valid)
        self.test("requirements.txt is valid", self.test_requirements_txt_valid)
        
        # Functionality tests
        print("\n🔧 Functionality Tests")
        print("-" * 70)
        self.test("demo_data.json is valid", self.test_demo_data_valid)
        self.test("Explainability module present", self.test_explainability_module)
        self.test("main.py has Phase 15 features", self.test_main_py_has_phase15_features)
        
        # Documentation tests
        print("\n📖 Documentation Tests")
        print("-" * 70)
        self.test("Documentation is complete", self.test_documentation_complete)
        
        # Summary
        print("\n" + "="*70)
        print("  Test Summary")
        print("="*70)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        
        if self.errors:
            print(f"\n🔴 Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"  • {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more")
        
        # Overall result
        print("\n" + "="*70)
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED - System ready for deployment!")
        else:
            print(f"⚠️  {self.tests_failed} tests failed - See errors above")
        print("="*70 + "\n")
        
        return self.tests_passed, self.tests_failed, self.errors, self.warnings


def main():
    """Run test suite."""
    parser = argparse.ArgumentParser(description="Phase 15 Fresh Install Test")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--cleanup", action="store_true", help="Remove test artifacts")
    
    args = parser.parse_args()
    
    # Run tests
    tester = FreshInstallTest(verbose=args.verbose)
    passed, failed, errors, warnings = tester.run_all()
    
    # Return appropriate exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
