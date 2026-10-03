# Historial de Cambios (Changelog)

Todas las modificaciones notables del proyecto Frondabrick están documentadas en este archivo.

## [1.0.0] - 2026-10-02

### Añadido
- **Fase 0 (Auditoría):** Matriz de capacidades reales de Antigravity en `docs/ANTIGRAVITY_CAPABILITIES.md` y experimento `experiments/EXP-001/` con dictamen PASS.
- **Fase 1 (F-Core):** Manifiesto `plugin.json` y 4 reglas base (`00-core.md`, `01-safety.md`, `02-workflow.md`, `03-testing.md`) en `.agents/plugins/frondabrick-core/` y `.agents/rules/`.
- **Fase 2 (F-Reviewer):** Agente de auditoría en modo estricto READ ONLY, definición de rol y matriz de permisos en `agents/reviewer/` y skill `fronda-reviewer`.
- **Fase 3 (F-Planner):** Agente de planificación arquitectónica sin capacidad de programación, plantilla de 10 secciones obligatorias y skill `fronda-planner`.
- **Fase 4 (F-Shield):** Motor de guardarraíles con 5 niveles de defensa, catálogo de patrones de seguridad y hook ejecutable `PreToolUse` en `scripts/security/` y `.agents/hooks.json`.
- **Fase 5 (Sistema de Evidencia):** Módulo `EvidenceRecorder` con persistencia física en `evidence/` (`session`, `security`, `tests`, `architecture`) bajo las 7 preguntas obligatorias.
- **Fase 6 (Test Harness):** Runner maestro `tests/run_all.py` y suite de integración.
- **Fase 7 (F-Memory):** Almacenamiento persistente controlado con flujo Observación -> Refuerzo -> Promoción (`confidence >= 0.7`) y catálogo de anti-patrones en `memory/`.
- **Fase 8 (F-Skills):** Catálogo de 6 habilidades operativas en `.agents/skills/` y `skills/` cumpliendo la regla de la Sección 20.
- **Fase 9 (F-Build-Resolver):** Especialista en resolución metódica de errores de compilador y tests mediante el ciclo de 7 pasos.
- **Fase 10 & 11 (F-Browser-QA & F-Fleet):** Protocolo de verificación visual en navegador y orquestador de flota con matriz de permisos en `docs/AGENT_PERMISSIONS.md`.
- **Fase 12 & 15 (CLI & Doctor):** Herramienta de línea de comandos `frondabrick.py` con subcomandos `doctor`, `validate`, `audit`, `shield`, `memory`, `init`.
- **Fase 13 (Red Team):** Suite de pruebas adversariales con 10 vectores de ataque (A01 a A10) neutralizados exitosamente.
- **Fase 14 (E2E):** Prueba de integración de ciclo de vida completo en entorno temporal local (tempfile/tempdir), reproducible en el arnés Python.
- **Documentación Completa (Sección 29):** Todos los 9 documentos normativos obligatorios redactados en `docs/`.

## [1.1.0] - 2026-10-02 (Bloque F17–F26.6)

### Demostrado y Consolidado
- **F17–F20 (Auditoría Runtime e Intercepción):** Refutación empírica de que el hook `DENY` o `exit != 0` anulen el proceso hijo en el runtime Windows de Antigravity. Delimitación formal de F-Shield como Policy & Audit Layer.
- **F21–F24 (Hardening NTFS y Autonomía):** Bóveda física protegida mediante ACL NTFS contra eliminación (`del`, `rmdir`, `Remove-Item`) bajo la identidad probada del usuario; supervivencia del canario con SHA-256 verificado y preservación de autonomía de desarrollo R/W/D en workspace mutable.
- **F25 (Resiliencia Operacional):** Supervivencia e integridad de la bóveda ante procesos abortados abruptamente, fallos TDD, interrupciones de edición y recuperación determinista.
- **F26 (Forense y Sellado):** Correlación de sesión (`session_id`, `PID`, Git, Vault, F-Shield), reconstructor determinista con preservación estricta de lagunas (`UNKNOWN`) y sellado criptográfico de integridad SHA-256 (`SEAL_VALID` vs `SEAL_TAMPERED`).
- **F26.6 (Auditoría de Consistencia):** Armonización de claims, corrección de sobreafirmaciones, validación de las 20 suites sin dependencias ocultas y congelamiento de estado verificado con 0 cambios funcionales.
