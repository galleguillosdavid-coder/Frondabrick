# Matriz de Realidad de Frondabrick: Reality Matrix

**Documento:** `docs/FRONDABRICK_REALITY_MATRIX.md`  
**Fase:** Fase 17 — Cierre de Brechas y Consolidación  
**Fecha:** 2026-10-02  
**Estado:** **OPERATIVO CON LIMITACIONES CONSOLIDADAS Y HONESTAS**  

---

## 1. Clasificación Rigurosa Anti-Alucinación (Post-Fase 17)

| Capacidad | Código | Test | Runtime Real | Evidencia Observable | Estado Final |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Rules** | ✓ | ✓ | ✓ | Ubicación única canónica `.agents/rules/` (duplicación en plugins eliminada). Inyección en prompt verificada. | **CANÓNICO / DEMOSTRADO** |
| **Skills** | ✓ | ✓ | ✓ | Ubicación canónica única `.agents/skills/` (eliminada carpeta raíz `skills/`). Progressive disclosure verificado. | **CANÓNICO / DEMOSTRADO** |
| **Hooks** | ✓ | ✓ | ✓ | Hook único canónico en `.agents/hooks.json` (eliminada doble invocación de plugin). Ejecución síncrona verificada. | **CANÓNICO / DEMOSTRADO** |
| **F-Shield (Detección)** | ✓ | ✓ | ✓ | Patrones ampliados contra bypasses (`del /q /s`, `Remove-Item -r`, `powershell -enc`). Falsos positivos filtrados (`git grep`, `echo`). | **HECHO / DEMOSTRADO** |
| **F-Shield (Bloqueo)** | ✓ | ✓ | ✗ | `DENY` es una compuerta normativa y veredicto de auditoría. El runtime IDE no cuenta con sandbox de kernel coercitivo de terminal. | **BARRERA NORMATIVA / NO COERCITIVO** |
| **Reviewer (Aislamiento)** | ✓ | ✓ | ✗ | `activeRole` no existe nativamente en el payload de Antigravity. La restricción de sólo lectura es una política declarativa y prompt. | **POLÍTICA DECLARADA / ARNÉS** |
| **Planner (No-Coding)** | ✓ | ✓ | ✗ | Plantilla de 10 secciones y skill presentes; directiva prompt estricta, sin barrera física de software. | **HECHO / POLÍTICA PROMPT** |
| **Memory (Archivos)** | ✓ | ✓ | ✓ | Módulo `MemoryManager` opera y persiste JSONs válidos en `memory/` con cálculo determinista de confianza. | **HECHO / TESTEADO INTERNAMENTE** |
| **Memory (Cognitivo)** | ✓ | ✓ | ✗ | Sin inyección automática en contexto ni detección de contradicciones en tiempo real. | **HIPÓTESIS** |
| **Fleet (Subagentes)** | ✓ | ✓ | ✗ | No existen subprocesos ni subagentes nativos concurrentes; son roles y skills operadas por un único agente. | **NO SOPORTADO (NATIVO)** |
| **Browser QA** | ✓ | ✓ | ✗ | Herramienta `browser_subagent` disponible en Antigravity, pero 0 ejecuciones activas del arnés. | **CONOCIDO / NO DEMOSTRADO** |
| **CLI (`frondabrick`)** | ✓ | ✓ | ✓ | Subcomandos `doctor`, `validate`, `audit`, `shield`, `memory` ejecutados con éxito en la máquina Windows. | **HECHO / DEMOSTRADO** |
| **E2E Lifecycle** | ✓ | ✓ | ✗ | `test_full_lifecycle_e2e.py` es una simulación 100% Python en un `tempdir`. | **E2E SIMULADO** |

---

## 2. Resumen Cuantitativo de Capacidades (Fase 17)

- **Capacidades Realmente Demostradas y Canónicas:** 4 (Rules, Skills, Invocación de Hooks, CLI local).
- **Capacidades de Detección y Auditoría Normativa:** 1 (F-Shield Detección + Bitácora; Bloqueo formalizado como auditoría, no como sandbox coercitivo).
- **Capacidades Internas / Simuladas en Python:** 4 (Gestión de archivos de memoria, Detección de errores en stack traces, E2E en tempdir, Red Team unitario).
- **Capacidades Declarativas / Políticas no Forzadas por Runtime:** 2 (Aislamiento de Reviewer, No-coding de Planner).
- **Capacidades No Demostradas:** 1 (Browser QA).
- **Capacidades No Soportadas Nativamente:** 1 (Subagentes declarativos aislados concurrentes).

---

## 3. Resoluciones Específicas de la Fase 17

1. **Eliminación de Duplicación:**
   - Hooks: Eliminado `.agents/plugins/frondabrick-core/hooks.json`. Canónico: `.agents/hooks.json`.
   - Reglas: Eliminado `.agents/plugins/frondabrick-core/rules/`. Canónico: `.agents/rules/`.
   - Skills: Eliminado `skills/` en raíz. Canónico: `.agents/skills/`.
2. **Cobertura de Falsos Negativos:**
   - `del /q /s` -> Detectado bajo `SEC-001`.
   - `Remove-Item -r` -> Detectado bajo `SEC-001`.
   - `powershell -enc` -> Detectado bajo `SEC-008` (Nivel 3 - ASK).
3. **Eliminación de Falsos Positivos:**
   - Comandos de inspección pasiva (`git grep`, `rg`, `grep`, `findstr`, `echo`, `cat`, `type`, `Select-String`) no son interceptados indiscriminadamente.
4. **Redefinición de `DENY`:**
   - Declarado explícitamente en `docs/SECURITY.md`, `scripts/security/policy.py` y matriz de realidad como compuerta de auditoría y veredicto normativo, evitando falsas garantías de seguridad.
5. **Integridad de Ficheros Protegidos:**
   - `chat gpt` y `gen.md` se mantienen inalterados (verificado por coincidencia byte a byte de SHA-1).
