# Matriz de Realidad de Frondabrick: Reality Matrix

**Documento:** `docs/FRONDABRICK_REALITY_MATRIX.md`  
**Fase:** Fase 16 — Auditoría Independiente  
**Fecha:** 2026-10-02  

---

## 1. Clasificación Rigurosa Anti-Alucinación

| Capacidad | Código | Test | Runtime Real | Evidencia Observable | Estado Final |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Rules** | ✓ | ✓ | ✓ | Descubrimiento de `.agents/rules/` por Antigravity e inyección jerárquica deduplicada. | **HECHO / DEMOSTRADO** |
| **Skills** | ✓ | ✓ | ✓ | Catálogo inyectado en prompt con progressive disclosure; lectura verificada mediante `view_file`. | **HECHO / DEMOSTRADO** |
| **Hooks** | ✓ | ✓ | ✓ | Ejecución síncrona demostrada en vivo; `scripts/security/validator.py` invocado en cada tool call. | **HECHO / DEMOSTRADO** |
| **F-Shield (Detección)** | ✓ | ✓ | ✓ | Análisis regex intercepta comandos en stdin y escribe en `evidence/security/audit.jsonl`. | **HECHO / DEMOSTRADO** |
| **F-Shield (Bloqueo)** | ✓ | ✓ | ✗ | El hook emitió `{"decision": "deny"}` en step 345, pero Antigravity continuó y ejecutó el comando en PowerShell. | **NO SOPORTADO / FAIL** |
| **Reviewer (Aislamiento)** | ✓ | ✓ | ✗ | `activeRole` no existe en Antigravity. La restricción de solo lectura fue probada sólo con mocks Python. | **HIPÓTESIS / POLÍTICA DECLARADA** |
| **Planner (No-Coding)** | ✓ | ✓ | ✗ | Plantilla de 10 secciones y skill presentes, pero ningún mecanismo técnico impide al modelo escribir código. | **HECHO / NO DEMOSTRADO** |
| **Memory (Archivos)** | ✓ | ✓ | ✓ | Módulo `MemoryManager` opera y persiste JSONs válidos en `memory/` con cálculo de confianza. | **HECHO / TESTEADO INTERNAMENTE** |
| **Memory (Cognitivo)** | ✓ | ✓ | ✗ | Sin inyección automática en contexto ni detección de contradicciones (Caso C no implementado). | **HIPÓTESIS** |
| **Fleet (Subagentes)** | ✓ | ✓ | ✗ | No existen subprocesos ni subagentes nativos concurrentes; son skills operadas por un único agente. | **NO SOPORTADO (NATIVO)** |
| **Browser QA** | ✓ | ✓ | ✗ | Herramienta `browser_subagent` disponible en Antigravity, pero 0 ejecuciones reales realizadas por el arnés. | **CONOCIDO / NO DEMOSTRADO** |
| **CLI (`frondabrick`)** | ✓ | ✓ | ✓ | Subcomandos `doctor`, `validate`, `audit`, `shield`, `memory` ejecutados con éxito en la máquina Windows. | **HECHO / DEMOSTRADO** |
| **E2E Lifecycle** | ✓ | ✓ | ✗ | `test_full_lifecycle_e2e.py` es una simulación 100% Python en un `tempdir`, sin interacción con Antigravity. | **E2E SIMULADO** |

---

## 2. Resumen Cuantitativo de Capacidades

- **Capacidades Realmente Demostradas en Runtime:** 4 (Rules, Skills, Invocación de Hooks, CLI local).
- **Capacidades Demostradas Parcialmente / Con Fallo de Bloqueo:** 1 (F-Shield Detección ejecutada, pero Bloqueo no respetado por el IDE).
- **Capacidades Solamente Internas / Simuladas en Python:** 4 (Gestión de archivos de memoria, Detección de errores en stack traces, E2E en tempdir, Red Team unitario).
- **Capacidades Declarativas / Políticas no Forzadas por Runtime:** 2 (Aislamiento de Reviewer, No-coding de Planner).
- **Capacidades No Demostradas:** 1 (Browser QA).
- **Capacidades No Soportadas Nativamente:** 1 (Subagentes declarativos aislados concurrentes).
