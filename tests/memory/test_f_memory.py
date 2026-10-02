#!/usr/bin/env python3
"""
Test Suite for Phase 7: F-Memory
Verifies directory structure, 8-field schema, promotion gates, and anti-patterns.
"""

import sys
import tempfile
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.memory.manager import MemoryManager, REQUIRED_MEMORY_FIELDS

def test_memory_directories_exist():
    memory_root = WORKSPACE_ROOT / "memory"
    assert memory_root.is_dir(), "memory/ directory must exist"
    for subdir in ["session", "candidates", "verified", "anti-patterns"]:
        assert (memory_root / subdir).is_dir(), f"memory/{subdir}/ must exist"
    print("[PASS] All memory subdirectories exist physically.")

def test_memory_lifecycle_and_promotion():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        mgr = MemoryManager(root_dir=temp_dir)

        # 1. Observation of candidate
        cand = mgr.observe(
            content="En Windows, comandos PowerShell deben evitar flags bash no portables",
            origin="test_run_1",
            domain="powershell",
            initial_confidence=0.3
        )

        assert cand["id"].startswith("MEM-")
        assert cand["status"] == "candidate"
        assert cand["confidence"] == 0.3

        for field in REQUIRED_MEMORY_FIELDS:
            assert field in cand, f"Field '{field}' missing from memory item"

        # 2. Attempt premature promotion (Anti-Pattern: no auto-promotion of isolated observation)
        promoted, reason, item = mgr.promote(cand["id"], threshold=0.7)
        assert not promoted, "Premature promotion should be rejected!"
        assert "insuficiente" in reason.lower()
        assert item["status"] == "candidate"

        # 3. Reinforcement (Repetition and confirmation)
        r1 = mgr.reinforce(cand["id"], delta=0.2)  # 0.3 + 0.2 = 0.5
        assert r1["confidence"] == 0.5

        r2 = mgr.reinforce(cand["id"], delta=0.25) # 0.5 + 0.25 = 0.75
        assert r2["confidence"] == 0.75

        # 4. Valid promotion
        promoted, reason, verified_item = mgr.promote(cand["id"], threshold=0.7)
        assert promoted, f"Promotion should have succeeded: {reason}"
        assert verified_item["status"] == "verified"
        assert (temp_dir / "verified" / f"{cand['id']}.json").is_file()
        assert not (temp_dir / "candidates" / f"{cand['id']}.json").exists(), "Old candidate file should be cleaned up"

        # 5. Anti-Pattern registration
        anti = mgr.flag_anti_pattern(
            content="No usar expresiones regulares con \\b después de caracteres que no son palabras (:)",
            origin="EXP-001 bug analysis",
            domain="regex"
        )
        assert anti["status"] == "anti-pattern"
        assert (temp_dir / "anti-patterns" / f"{anti['id']}.json").is_file()

        # 6. Retrieve verified
        verified_list = mgr.get_verified(domain="powershell")
        assert len(verified_list) == 1
        assert verified_list[0]["id"] == cand["id"]

        print("[PASS] Full memory lifecycle (observe -> reinforce -> promote gate -> anti-pattern) verified.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        test_memory_directories_exist()
        test_memory_lifecycle_and_promotion()
        print("\n=== FASE 7: F-MEMORY TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Memory: {e}")
        sys.exit(1)
