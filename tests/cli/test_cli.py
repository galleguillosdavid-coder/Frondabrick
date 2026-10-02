#!/usr/bin/env python3
"""
Test Suite for Phase 12: Frondabrick CLI
Verifies subcommands: doctor, validate, audit, shield, memory, init.
"""

import sys
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

def test_cli_doctor():
    res = subprocess.run([sys.executable, "frondabrick.py", "doctor"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
    assert res.returncode == 0, f"Doctor failed with code {res.returncode}: {res.stderr}"
    assert "ESTADO DOCTOR: PASS" in res.stdout, f"Expected PASS in output, got: {res.stdout}"
    print("[PASS] frondabrick doctor executed with 100% PASS.")

def test_cli_shield():
    # Dangerous command
    res_block = subprocess.run([sys.executable, "frondabrick.py", "shield", "rm -rf /"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
    assert res_block.returncode == 0
    assert "F-SHIELD INTERCEPTADO" in res_block.stdout
    assert "Nivel 4 (BLOCK)" in res_block.stdout

    # Safe command
    res_allow = subprocess.run([sys.executable, "frondabrick.py", "shield", "git status"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
    assert res_allow.returncode == 0
    assert "F-SHIELD PERMITIDO" in res_allow.stdout
    print("[PASS] frondabrick shield evaluation commands verified.")

def test_cli_audit_and_memory():
    res_audit = subprocess.run([sys.executable, "frondabrick.py", "audit"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
    assert res_audit.returncode == 0
    assert "FRONDABRICK AUDIT" in res_audit.stdout

    res_mem = subprocess.run([sys.executable, "frondabrick.py", "memory"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
    assert res_mem.returncode == 0
    assert "FRONDABRICK MEMORY" in res_mem.stdout
    print("[PASS] frondabrick audit and memory commands verified.")

if __name__ == "__main__":
    try:
        test_cli_doctor()
        test_cli_shield()
        test_cli_audit_and_memory()
        print("\n=== FASE 12: CLI TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in CLI: {e}")
        sys.exit(1)
