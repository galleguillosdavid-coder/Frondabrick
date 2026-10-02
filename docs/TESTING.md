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
El runner unificado procesa 12 suites deterministas:
1. `tests/core/test_f_core.py`: Manifiesto y 4 reglas base.
2. `tests/reviewer/test_f_reviewer.py`: Aislamiento de solo lectura.
3. `tests/planner/test_f_planner.py`: Contrato de 10 secciones de planes.
4. `tests/shield/test_f_shield.py`: 5 niveles de defensa y patrones de seguridad.
5. `tests/evidence/test_evidence.py`: Jerarquía y las 7 preguntas obligatorias.
6. `tests/memory/test_f_memory.py`: Esquema de 8 campos y umbrales de promoción.
7. `tests/skills/test_skills.py`: Validación de la regla de la Sección 20.
8. `tests/resolver/test_f_build_resolver.py`: Ciclo de 7 pasos y anti-falso PASS.
9. `tests/fleet/test_f_fleet.py`: Matriz de permisos de los 7 roles.
10. `tests/cli/test_cli.py`: Comandos de la CLI `frondabrick`.
11. `tests/adversarial/test_red_team.py`: Neutralización de 10 vectores de ataque (A01 a A10).
12. `tests/e2e/test_full_lifecycle_e2e.py`: Ciclo completo E2E aislado y reproducible.
