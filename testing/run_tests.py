#!/usr/bin/env python
"""
=============================================================================
StudyAI — Unified Test Runner & Quality Suite (Member 4: Testing & QA)
=============================================================================
Usage:
    python testing/run_tests.py --all           # Run full suite (Unit, Security, AI, Acceptance)
    python testing/run_tests.py --unit          # Run unit & API tests
    python testing/run_tests.py --security      # Run authentication & security tests
    python testing/run_tests.py --ai            # Run AI evaluation benchmarks
    python testing/run_tests.py --acceptance    # Run end-to-end acceptance tests
=============================================================================
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
TESTING_DIR = WORKSPACE_ROOT / "testing"

# Ensure root, backend, and ai_integration are on sys.path
for p in [str(WORKSPACE_ROOT), str(BACKEND_DIR), str(WORKSPACE_ROOT / "ai_integration")]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyai_backend.settings')

def get_python_exe():
    venv_py = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable

def run_command(cmd, desc):
    print(f"\n{'='*70}")
    print(f"  RUNNING: {desc}")
    print(f"{'='*70}")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{WORKSPACE_ROOT};{BACKEND_DIR};{WORKSPACE_ROOT / 'ai_integration'}"
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), env=env)
    return res.returncode == 0

def run_unit_tests():
    py = get_python_exe()
    cmd = [py, str(BACKEND_DIR / "manage.py"), "test", "api.tests", "api.test_ocr", "--keepdb"]
    return run_command(cmd, "Django Unit & OCR Subsystem Tests")

def run_ocr_tests():
    py = get_python_exe()
    cmd = [py, str(BACKEND_DIR / "manage.py"), "test", "api.test_ocr", "--keepdb"]
    return run_command(cmd, "OCR Subsystem Reliability Tests")

def run_security_tests():
    py = get_python_exe()
    cmd = [py, str(BACKEND_DIR / "manage.py"), "test", "api.test_auth", "api.test_security", "--keepdb"]
    return run_command(cmd, "Security & Auth Verification Suite")


def run_ai_evaluation():
    py = get_python_exe()
    script = TESTING_DIR / "ai_evaluation" / "run_ai_evaluation.py"
    if not script.exists():
        print(f"[!] AI Evaluation script not found at {script}")
        return False
    cmd = [py, str(script)]
    return run_command(cmd, "AI Model Evaluation & Benchmarking")

def run_acceptance_tests():
    py = get_python_exe()
    script = TESTING_DIR / "acceptance" / "run_comprehensive_acceptance.py"
    if not script.exists():
        print(f"[!] Acceptance script not found at {script}")
        return False
    cmd = [py, str(script)]
    return run_command(cmd, "Comprehensive End-to-End Acceptance Tests")

def main():
    parser = argparse.ArgumentParser(description="StudyAI Unified Test Suite Runner")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--unit", action="store_true", help="Run Django unit tests")
    parser.add_argument("--ocr", action="store_true", help="Run OCR subsystem tests")
    parser.add_argument("--security", action="store_true", help="Run auth & security tests")
    parser.add_argument("--ai", action="store_true", help="Run AI evaluation benchmark")
    parser.add_argument("--acceptance", action="store_true", help="Run acceptance tests")

    args = parser.parse_args()

    # Default to unit + security if no flag given
    if not any([args.all, args.unit, args.ocr, args.security, args.ai, args.acceptance]):
        args.unit = True
        args.security = True

    results = {}

    if args.ocr:
        results["OCR Subsystem Tests"] = run_ocr_tests()

    if args.all or args.unit:
        results["Unit & OCR Tests"] = run_unit_tests()


    if args.all or args.security:
        results["Security Tests"] = run_security_tests()

    if args.all or args.ai:
        results["AI Evaluation"] = run_ai_evaluation()

    if args.all or args.acceptance:
        results["Acceptance Tests"] = run_acceptance_tests()

    print(f"\n{'='*70}")
    print("  TEST RESULTS SUMMARY")
    print(f"{'='*70}")
    all_passed = True
    for suite, passed in results.items():
        status = "PASSED [OK]" if passed else "FAILED [X]"
        print(f"  - {suite:30} : {status}")
        if not passed:
            all_passed = False
    print(f"{'='*70}\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
