#!/usr/bin/env python3
"""
Frondabrick Full E2E Lifecycle Test (Phase 14)
Executes a realistic user request in an isolated test workspace:
USER REQUEST -> PLANNER -> PLAN -> BUILDER -> F-SHIELD -> TEST -> REVIEWER -> EVIDENCE -> MEMORY -> FINAL
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.security.policy import ShieldPolicyEngine
from scripts.memory.manager import MemoryManager
from scripts.evidence.recorder import EvidenceRecorder
from scripts.fleet.orchestrator import FleetOrchestrator
from tests.planner.test_f_planner import MANDATORY_SECTIONS

def test_reproducible_e2e_lifecycle():
    sandbox_dir = Path(tempfile.mkdtemp(prefix="frondabrick_e2e_"))
    try:
        print("\n--- INICIO DE PRUEBA E2E AISLADA ---")
        print(f"Directorio sandbox: {sandbox_dir}")

        # 1. USER REQUEST
        user_request = "Implementar un formateador seguro de nombres de usuario"
        print(f"[Paso 1: USER REQUEST] -> '{user_request}'")

        # 2. PLANNER
        auth_planner, _ = FleetOrchestrator.authorize_tool_for_role("planner", "write_to_file", target_file="docs/plan.md")
        assert auth_planner, "Planner must be authorized to write plan docs"

        plan_content = """# PLAN: Formateador Seguro de Nombres de Usuario

## 1. OBJETIVO
Normalizar y sanitizar cadenas de texto para nombres de usuario.

## 2. ALCANCE
- Función `sanitize_username(name: str) -> str`.
- Eliminación de caracteres peligrosos y longitud máxima 30.

## 3. NO-ALCANCE
- Autenticación o almacenamiento en base de datos.

## 4. ARCHIVOS
- A crear: `src/username.py`, `tests/test_username.py`.

## 5. DEPENDENCIAS
- Librería estándar `re`.

## 6. RIESGOS
- Normalización excesiva que altere nombres legítimos.

## 7. PLAN
1. Redactar pruebas unitarias en `test_username.py`.
2. Implementar `sanitize_username` en `username.py`.
3. Ejecutar pruebas.

## 8. TESTS
- Test de caracteres alfanuméricos válidos.
- Test de inyección de caracteres de control o SQL.

## 9. CRITERIOS DE ACEPTACIÓN
- [ ] 100% tests en PASS.
- [ ] No admite caracteres no permitidos.

## 10. ROLLBACK
- Eliminar `src/username.py` si la prueba falla.
"""
        # Validate 10 mandatory sections
        for sec in MANDATORY_SECTIONS:
            assert sec in plan_content, f"Plan missing mandatory section: {sec}"
        print("[Paso 2: PLANNER -> PLAN] -> Generado plan válido con las 10 secciones obligatorias.")

        # 3. BUILDER & F-SHIELD INTERCEPTION
        auth_builder, _ = FleetOrchestrator.authorize_tool_for_role("builder", "write_to_file")
        assert auth_builder, "Builder must have write authorization"

        # Builder tries dangerous action first -> SHIELD blocks it
        dangerous_call = {
            "toolCall": {"name": "run_command", "args": {"CommandLine": "del /s c:\\sandbox"}},
            "activeRole": "builder"
        }
        shield_decision = ShieldPolicyEngine.evaluate(dangerous_call)
        assert shield_decision["decision"] == "deny", "F-Shield must block dangerous call!"
        print("[Paso 3: F-SHIELD] -> Comando destructivo interceptado y bloqueado.")

        # Builder performs valid code writing
        src_dir = sandbox_dir / "src"
        test_dir = sandbox_dir / "tests"
        src_dir.mkdir(parents=True)
        test_dir.mkdir(parents=True)

        code_file = src_dir / "username.py"
        code_file.write_text(
            "import re\n\ndef sanitize_username(name: str) -> str:\n    return re.sub(r'[^a-zA-Z0-9_]', '', name)[:30]\n",
            encoding="utf-8"
        )

        test_file = test_dir / "test_username.py"
        test_file.write_text(
            "from src.username import sanitize_username\n\ndef test_sanitize():\n    assert sanitize_username('User_123!') == 'User_123'\n    assert len(sanitize_username('a' * 50)) == 30\n",
            encoding="utf-8"
        )
        print("[Paso 4: BUILDER] -> Código de producción y pruebas creados.")

        # 4. TEST EXECUTION
        test_runner_script = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.')))
from tests.test_username import test_sanitize
test_sanitize()
print("E2E_TESTS_OK")
"""
        proc = subprocess.run(
            [sys.executable, "-c", test_runner_script],
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True
        )
        assert proc.returncode == 0, f"Tests failed: {proc.stderr}"
        assert "E2E_TESTS_OK" in proc.stdout
        print("[Paso 5: TEST] -> Pruebas unitarias ejecutadas con éxito (código de salida 0).")

        # 5. REVIEWER AUDIT
        auth_reviewer_write, _ = FleetOrchestrator.authorize_tool_for_role("reviewer", "write_to_file")
        assert not auth_reviewer_write, "Reviewer must be strictly READ ONLY"
        print("[Paso 6: REVIEWER] -> Auditoría completada. Regla de solo lectura verificada.")

        # 6. EVIDENCE RECORDING
        recorder = EvidenceRecorder(root_dir=sandbox_dir / "evidence")
        evidence_file = recorder.record("session", {
            "what": "Implementación de sanitize_username en sandbox E2E",
            "why": "Verificación del flujo completo de ciclo de vida",
            "files_changed": ["src/username.py", "tests/test_username.py"],
            "command_executed": "python -c 'test_sanitize()'",
            "result": "PASS",
            "tests_passed": ["test_sanitize"],
            "tests_failed": []
        }, title="E2E Lifecycle Proof")
        assert evidence_file.is_file()
        print(f"[Paso 7: EVIDENCE] -> Evidencia registrada con las 7 preguntas en: {evidence_file.name}")

        # 7. MEMORY ACCUMULATION
        mem_mgr = MemoryManager(root_dir=sandbox_dir / "memory")
        mem_item = mem_mgr.observe(
            content="La función sanitize_username garantiza longitud máxima 30 caracteres alfanuméricos",
            origin="e2e_run",
            domain="validation",
            initial_confidence=0.5
        )
        # Reinforce and promote
        mem_mgr.reinforce(mem_item["id"], delta=0.3)
        promoted, _, verified_mem = mem_mgr.promote(mem_item["id"], threshold=0.7)
        assert promoted
        assert verified_mem["status"] == "verified"
        print(f"[Paso 8: MEMORY] -> Patrón consolidado y promovido a memoria verificada ({verified_mem['id']}).")

        # 8. FINAL
        print("[Paso 9: FINAL] -> Flujo E2E completado exitosamente y 100% reproducible.")
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        test_reproducible_e2e_lifecycle()
        print("\n=== FASE 14: E2E LIFECYCLE TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] E2E Lifecycle failure: {e}")
        sys.exit(1)
