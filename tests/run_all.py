#!/usr/bin/env python3
"""
Frondabrick Master Test Runner
Discovers and executes all test suites across:
- tests/core/
- tests/shield/
- tests/reviewer/
- tests/planner/
- tests/integration/
Enforces: NO TEST = NO FINALIZADO
Persists execution evidence to evidence/tests/
"""

import sys
import os
import subprocess
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.recorder import EvidenceRecorder

TEST_SUITES = [
    ("Core", WORKSPACE_ROOT / "tests" / "core" / "test_f_core.py"),
    ("Reviewer", WORKSPACE_ROOT / "tests" / "reviewer" / "test_f_reviewer.py"),
    ("Planner", WORKSPACE_ROOT / "tests" / "planner" / "test_f_planner.py"),
    ("Shield", WORKSPACE_ROOT / "tests" / "shield" / "test_f_shield.py"),
    ("Evidence", WORKSPACE_ROOT / "tests" / "evidence" / "test_evidence.py"),
    ("Memory", WORKSPACE_ROOT / "tests" / "memory" / "test_f_memory.py"),
    ("Skills", WORKSPACE_ROOT / "tests" / "skills" / "test_skills.py"),
    ("Resolver", WORKSPACE_ROOT / "tests" / "resolver" / "test_f_build_resolver.py"),
    ("Fleet", WORKSPACE_ROOT / "tests" / "fleet" / "test_f_fleet.py"),
    ("CLI", WORKSPACE_ROOT / "tests" / "cli" / "test_cli.py"),
    ("RedTeam", WORKSPACE_ROOT / "tests" / "adversarial" / "test_red_team.py"),
    ("Vault", WORKSPACE_ROOT / "tests" / "vault" / "test_vault_hardening.py"),
    ("E2E", WORKSPACE_ROOT / "tests" / "e2e" / "test_full_lifecycle_e2e.py"),
    ("Integration", WORKSPACE_ROOT / "tests" / "integration" / "test_pipeline_integration.py"),
]

def run_all_suites():
    print("=" * 60)
    print("FRONDABRICK MASTER TEST HARNESS — EJECUCIÓN TOTAL")
    print("=" * 60)

    passed_suites = []
    failed_suites = []
    start_time = time.time()

    for name, suite_path in TEST_SUITES:
        print(f"\n[EJECUTANDO] Suite: {name} ({suite_path.name})...")
        if not suite_path.is_file():
            print(f"[FAIL] Suite no encontrada: {suite_path}")
            failed_suites.append(name)
            continue

        result = subprocess.run(
            [sys.executable, str(suite_path)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )

        if result.returncode == 0:
            print(f"[PASS] Suite {name} completada con éxito.")
            passed_suites.append(name)
        else:
            print(f"[FAIL] Suite {name} falló (código {result.returncode}):")
            print(result.stdout)
            print(result.stderr)
            failed_suites.append(name)

    duration = time.time() - start_time
    total = len(TEST_SUITES)
    overall_status = "PASS" if len(failed_suites) == 0 else "FAIL"

    print("\n" + "=" * 60)
    print(f"RESUMEN FINAL: {len(passed_suites)}/{total} SUITES APROBADAS ({overall_status})")
    print(f"TIEMPO TOTAL: {duration:.2f}s")
    print("=" * 60)

    # Persist evidence
    recorder = EvidenceRecorder(root_dir=WORKSPACE_ROOT / "evidence")
    evidence_payload = {
        "what": f"Ejecución maestra del test harness ({len(passed_suites)}/{total} suites)",
        "why": "Verificación periódica obligatoria de integridad del arnés (No Test = No Finalizado)",
        "files_changed": [],
        "command_executed": "python tests/run_all.py",
        "result": overall_status,
        "tests_passed": passed_suites,
        "tests_failed": failed_suites,
        "metadata": {
            "duration_seconds": round(duration, 2),
            "suite_count": total
        }
    }
    evidence_file = recorder.record("tests", evidence_payload, title=f"Harness Run {overall_status}")
    print(f"\n[EVIDENCIA REGISTRADA] Guardada en: {evidence_file.name}")

    if overall_status == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_all_suites()
