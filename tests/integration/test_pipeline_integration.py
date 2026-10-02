#!/usr/bin/env python3
"""
Integration Test Suite for Frondabrick Harness (Phase 6)
Validates the complete pipeline integration:
Planner -> F-Shield Guardrail -> Builder -> Reviewer Audit -> Evidence Recording
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.security.policy import ShieldPolicyEngine
from scripts.evidence.recorder import EvidenceRecorder
from tests.planner.test_f_planner import MANDATORY_SECTIONS

def test_full_pipeline_flow():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Step 1: PLANNER produces a 10-section specification
        plan_doc = """# PLAN: Implementar Cache de Consultas

## 1. OBJETIVO
Acelerar la resolución de consultas recurrentes reduciendo latencia.

## 2. ALCANCE
- Implementación de LRU cache en memoria.
- Tests unitarios con TTL.

## 3. NO-ALCANCE
- Persistencia en Redis externa.

## 4. ARCHIVOS
- A crear: src/cache.py
- A modificar: src/query_engine.py

## 5. DEPENDENCIAS
- Librería estándar functools y time.

## 6. RIESGOS
- Desborde de memoria si el tamaño máximo no está acotado.

## 7. PLAN
1. Diseñar interfaz Cache.
2. Implementar decorador lru_cache.
3. Añadir suite de tests.

## 8. TESTS
- Test de acierto de cache (hit).
- Test de fallo y expiración (miss/ttl).

## 9. CRITERIOS DE ACEPTACIÓN
- [ ] 100% de tests unitarios aprobados.
- [ ] Tiempo de respuesta < 5ms en cache hit.

## 10. ROLLBACK
- Revertir cambios mediante `git checkout -- src/query_engine.py`.
"""
        # Validate that plan contains all 10 mandatory sections
        for section in MANDATORY_SECTIONS:
            assert section in plan_doc, f"Plan is missing section: {section}"

        # Step 2: F-SHIELD intercepts dangerous attempts during build phase
        dangerous_attempt = {
            "toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf src/backup"}},
            "activeRole": "builder"
        }
        guardrail_decision = ShieldPolicyEngine.evaluate(dangerous_attempt)
        assert guardrail_decision["decision"] == "deny", "F-Shield must block dangerous deletion!"

        # Step 3: BUILDER performs legitimate write
        safe_attempt = {
            "toolCall": {"name": "run_command", "args": {"CommandLine": "python -m pytest"}},
            "activeRole": "builder"
        }
        safe_decision = ShieldPolicyEngine.evaluate(safe_attempt)
        assert safe_decision["decision"] == "allow", "Safe execution must be allowed!"

        # Step 4: REVIEWER audits the diff and verifies read-only constraint
        reviewer_write_attempt = {
            "toolCall": {"name": "write_to_file", "args": {"TargetFile": "src/cache.py"}},
            "activeRole": "reviewer"
        }
        reviewer_decision = ShieldPolicyEngine.evaluate(reviewer_write_attempt)
        assert reviewer_decision["decision"] == "deny", "Reviewer must be prevented from writing!"

        # Step 5: EVIDENCE is persisted answering the 7 mandatory questions
        recorder = EvidenceRecorder(root_dir=temp_dir)
        evidence_payload = {
            "what": "Ejecución E2E de pipeline plan-build-review",
            "why": "Verificar integración entre Planner, Shield, Builder y Reviewer",
            "files_changed": ["src/cache.py"],
            "command_executed": "python tests/run_all.py",
            "result": "PASS",
            "tests_passed": ["test_plan_sections", "test_shield_block", "test_reviewer_isolation"],
            "tests_failed": []
        }
        saved_evidence = recorder.record("architecture", evidence_payload, title="E2E Pipeline Integration")
        assert saved_evidence.is_file()

        with open(saved_evidence, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        assert persisted["evidence"]["result"] == "PASS"

        print("[PASS] Full lifecycle integration (Planner -> Shield -> Builder -> Reviewer -> Evidence) verified.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_full_pipeline_flow()
    print("\n=== FASE 6: INTEGRATION TEST PASSED (100%) ===")
    sys.exit(0)
