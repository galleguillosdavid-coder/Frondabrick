#!/usr/bin/env python3
"""
Test Suite for Phase 9: F-Build-Resolver
Verifies error trace parsing, 7-step resolution protocol, and anti-fake PASS rules.
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.resolver.engine import BuildResolverEngine, RESOLVER_STEPS

ROLE_FILE = WORKSPACE_ROOT / "agents" / "build_resolver" / "ROLE.md"

def test_role_and_7_steps_definition():
    assert ROLE_FILE.is_file(), f"ROLE.md missing at {ROLE_FILE}"
    content = ROLE_FILE.read_text(encoding="utf-8")
    for step in ["REPRODUCIR", "LOCALIZAR", "EXPLICAR", "PROPONER", "CORREGIR", "VOLVER A EJECUTAR", "DEMOSTRAR SOLUCIÓN"]:
        assert step in content, f"ROLE.md missing required step: {step}"
    assert "Anti-Falso PASS" in content or "anti-falso" in content.lower()
    print("[PASS] F-Build-Resolver role and 7 mandatory steps verified.")

def test_trace_parsing():
    sample_trace = """Traceback (most recent call last):
  File "C:\\Users\\Frondabrick\\Desktop\\dvd\\EvryThing\\tests\\shield\\test_f_shield.py", line 54, in test_mandatory_detections
    assert r is not None and r["id"] == "SEC-002"
AssertionError: Expected SEC-002 match
"""
    parsed = BuildResolverEngine.parse_error_trace(sample_trace)
    assert parsed["line"] == 54
    assert "test_f_shield.py" in parsed["file"]
    assert parsed["error_type"] == "AssertionError"
    assert "Expected SEC-002 match" in parsed["message"]
    print("[PASS] Stack trace parsing and error localization verified.")

def test_resolution_cycle_validation():
    # 1. Incomplete report (missing 'proof')
    incomplete_report = {
        "reproduce": "python tests/shield/test_f_shield.py -> Exit code 1",
        "locate": "scripts/security/detector.py:30",
        "explain": "Regex word boundary trailing colon failed to match format d:",
        "propose": "Update regex pattern to include specific word boundaries on commands",
        "fix": "Modified pattern in detector.py",
        "rerun": {"exit_code": 0, "stdout": "All tests passed"}
    }
    res_inc = BuildResolverEngine.evaluate_resolution_cycle(incomplete_report)
    assert res_inc["status"] == "FAIL"
    assert "proof" in res_inc["reason"]

    # 2. Rerun failed with exit code 1
    failed_rerun = dict(incomplete_report)
    failed_rerun["proof"] = "Observación de terminal"
    failed_rerun["rerun"] = {"exit_code": 1, "stdout": "Test still failing"}
    res_failed = BuildResolverEngine.evaluate_resolution_cycle(failed_rerun)
    assert res_failed["status"] == "FAIL"
    assert "falló con código 1" in res_failed["reason"]

    # 3. Legitimate complete report
    valid_report = dict(incomplete_report)
    valid_report["proof"] = "Ejecución de test_f_shield.py con código de salida 0 y aserciones en verde sin regresiones."
    valid_report["rerun"] = {"exit_code": 0, "stdout": "All 7 tests passed (100% PASS)"}
    res_valid = BuildResolverEngine.evaluate_resolution_cycle(valid_report)
    assert res_valid["status"] == "RESOLVED"
    print("[PASS] Full 7-step resolution protocol and anti-fake PASS gating verified.")

if __name__ == "__main__":
    try:
        test_role_and_7_steps_definition()
        test_trace_parsing()
        test_resolution_cycle_validation()
        print("\n=== FASE 9: F-BUILD-RESOLVER TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Build-Resolver: {e}")
        sys.exit(1)
