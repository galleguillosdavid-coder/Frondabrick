#!/usr/bin/env python3
"""
Test Suite for Phase 5: Evidence System
Verifies folder hierarchy, enforcement of the 7 mandatory questions, and persistence.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.recorder import EvidenceRecorder, MANDATORY_EVIDENCE_FIELDS, CATEGORIES

def test_directories_exist():
    evidence_root = WORKSPACE_ROOT / "evidence"
    assert evidence_root.is_dir(), "evidence/ directory must exist"
    for cat in CATEGORIES:
        cat_dir = evidence_root / cat
        assert cat_dir.is_dir(), f"evidence/{cat}/ directory must exist"
    print(f"[PASS] All {len(CATEGORIES)} evidence subdirectories exist.")

def test_enforce_7_questions_schema():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        recorder = EvidenceRecorder(root_dir=temp_dir)

        # Incomplete data (missing 'result' and 'tests_failed')
        bad_data = {
            "what": "Refactor de módulo de seguridad",
            "why": "Eliminar vulnerabilidad de word boundary",
            "files_changed": ["scripts/security/detector.py"],
            "command_executed": "python tests/shield/test_f_shield.py",
            "tests_passed": ["test_mandatory_detections"]
        }

        try:
            recorder.record("security", bad_data, title="Incomplete Test")
            assert False, "Recording without all 7 mandatory fields should have failed!"
        except ValueError as e:
            assert "result" in str(e) and "tests_failed" in str(e)

        # Complete valid data
        good_data = {
            "what": "Refactor de módulo de seguridad",
            "why": "Eliminar vulnerabilidad de word boundary",
            "files_changed": ["scripts/security/detector.py"],
            "command_executed": "python tests/shield/test_f_shield.py",
            "result": "PASS",
            "tests_passed": ["test_mandatory_detections", "test_defense_levels"],
            "tests_failed": []
        }

        saved_path = recorder.record("security", good_data, title="Prueba Valida")
        assert saved_path.is_file(), f"Saved evidence file missing at {saved_path}"

        with open(saved_path, "r", encoding="utf-8") as f:
            persisted = json.load(f)

        for field in MANDATORY_EVIDENCE_FIELDS:
            assert field in persisted["evidence"], f"Field '{field}' missing from persisted evidence"

        assert persisted["evidence"]["result"] == "PASS"
        print("[PASS] Enforcement of the 7 mandatory evidence questions verified.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_recording_across_all_categories():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        recorder = EvidenceRecorder(root_dir=temp_dir)
        sample_payload = {
            "what": "Verificación de integración",
            "why": "Validar flujo de auditoría",
            "files_changed": [],
            "command_executed": "pytest",
            "result": "SUCCESS",
            "tests_passed": ["t1", "t2"],
            "tests_failed": []
        }

        for cat in CATEGORIES:
            path = recorder.record(cat, sample_payload, title=f"Audit {cat}")
            assert path.is_file(), f"Record for category {cat} failed to write"
            records = recorder.list_records(cat)
            assert len(records) >= 1

        print(f"[PASS] Successfully recorded and listed evidence across all {len(CATEGORIES)} categories.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        test_directories_exist()
        test_enforce_7_questions_schema()
        test_recording_across_all_categories()
        print("\n=== FASE 5: EVIDENCE SYSTEM TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in Evidence System: {e}")
        sys.exit(1)
