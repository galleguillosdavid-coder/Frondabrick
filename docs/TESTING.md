# Marco de Pruebas y Aserciones (Test Harness)

**Documento:** `docs/TESTING.md`  
**Módulo Responsable:** Test Harness  

---

## 1. Axioma Rector: NO TEST = NO FINALIZADO
Ninguna regla, módulo, agente o característica se considera implementada en Frondabrick sin una suite de pruebas reproducible que verifique sus aserciones.

---

## 2. Los 4 Estados Formales Permitidos
Queda prohibido utilizar expresiones ambiguas como "parece que funciona" o "debería pasar". Los únicos estados reconocidos son:
- **PASS:** Ejecución completada con código de salida 0 y evidencia observable de aserciones en verde.
- **FAIL:** Error en runtime o fallo en una o más aserciones. Exige detención inmediata, aislamiento y corrección.
- **INCONCLUSIVE:** Factores externos o precondiciones incompletas impiden dictaminar el resultado.
- **NOT_SUPPORTED:** Característica evaluada que el entorno/antigravity no soporta nativamente.

---

## 3. Cobertura del Harness Maestro (`tests/run_all.py`)
El runner unificado procesa 20 suites deterministas y reproducibles:
1. `tests/core/test_f_core.py`: Manifiesto, reglas base e integridad de archivos fundacionales.
2. `tests/reviewer/test_f_reviewer.py`: Evaluación normativa de solo lectura del rol Reviewer.
3. `tests/planner/test_f_planner.py`: Contrato de 10 secciones de planes técnicos.
4. `tests/shield/test_f_shield.py`: 5 niveles de defensa, patrones de seguridad y descarte de falsos positivos.
5. `tests/evidence/test_evidence.py`: Jerarquía física y las 7 preguntas obligatorias.
6. `tests/memory/test_f_memory.py`: Esquema de 8 campos, acumulación de confianza y anti-patrones.
7. `tests/skills/test_skills.py`: Validación de la regla de estructura de la Sección 20.
8. `tests/resolver/test_f_build_resolver.py`: Ciclo de 7 pasos y anti-falso PASS.
9. `tests/fleet/test_f_fleet.py`: Matriz de permisos de los 7 roles.
10. `tests/cli/test_cli.py`: Comandos de la CLI `frondabrick`.
11. `tests/adversarial/test_red_team.py`: Neutralización de 10 vectores de ataque (A01 a A10).
12. `tests/vault/test_vault_hardening.py`: Bóveda física, canario NTFS, auditoría de ACL y deriva (F22–F23).
13. `tests/vault/test_resilience_session.py`: Resiliencia ante abortos, fallos TDD, interrupciones y auto-recuperación (F25).
14. `tests/forensics/test_f26_correlation.py`: Correlación de sesión (session_id, PID, Git, Vault, F-Shield) (EXP-26.1).
15. `tests/forensics/test_f26_reconstructor.py`: Reconstructor forense determinista y clasificación de lagunas UNKNOWN (EXP-26.2).
16. `tests/forensics/test_f26_blocked.py`: Trazabilidad y separación arquitectónica de intento hostil bloqueado (EXP-26.3).
17. `tests/forensics/test_f26_allowed.py`: Trazabilidad de operación de desarrollo mutable legítima (EXP-26.4).
18. `tests/forensics/test_f26_seal.py`: Sello criptográfico SHA-256 y detección de alteraciones posteriores (EXP-26.5).
19. `tests/e2e/test_full_lifecycle_e2e.py`: Ciclo de vida completo simulado en entorno temporal local (tempdir).
20. `tests/integration/test_pipeline_integration.py`: Integración de flujo completo en entorno temporal local.
