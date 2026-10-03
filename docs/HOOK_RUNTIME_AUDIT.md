# Auditoría del Runtime de Hooks de Antigravity: Hook Runtime Audit

**Documento:** `docs/HOOK_RUNTIME_AUDIT.md`  
**Fase:** Fase 16 — Auditoría Independiente  
**Fecha:** 2026-10-02  
**Archivos Auditados:**
- `.agents/hooks.json`
- `.agents/plugins/frondabrick-core/hooks.json`
- `scripts/security/validator.py`
- `evidence/security/audit.jsonl`

---

## 1. Experimento en Vivo: Intercepción Real vs Ejecución Real

### Metodología de la Prueba en Vivo
1. Se creó un directorio centinela con un archivo testigo:
   `sentinel_test_dir\sentinel.txt` (verificado como `True`).
2. El agente invocó la herramienta `run_command` con el comando destructivo `rm -rf sentinel_test_dir`.
3. Se inspeccionaron la bitácora viva `evidence/security/audit.jsonl`, la traza de la sesión y el resultado de la terminal.

### Hallazgos Empíricos Observados

```text
                                Antigravity IDE (Tool Call: run_command)
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
             Hook 1 (.agents/hooks.json)                 Hook 2 (plugin frondabrick-core)
                         |                                                 |
                         v                                                 v
               validator.py (stdin)                              validator.py (stdin)
                         |                                                 |
                         v                                                 v
           audit.jsonl: stepIdx 345                          audit.jsonl: stepIdx 345
           decision: "deny" (Nivel 4)                        decision: "deny" (Nivel 4)
                         |                                                 |
                         +------------------------+------------------------+
                                                  |
                                                  v
                     [¿Se bloqueó la herramienta en Antigravity?]
                                                  |
                                       NO: LA EJECUCIÓN CONTINUÓ
                                                  |
                                                  v
                                      PowerShell Terminal Ejecutó:
                                      "rm -rf sentinel_test_dir"
                                                  |
                                                  v
                                  Fallo nativo de sintaxis de PowerShell:
                                  "NamedParameterNotFound: ParameterBindingException"
```

### Respuestas a las Preguntas Mandatorias de la Auditoría (Sección 5)
1. **¿El hook se ejecutó?**  
   **SÍ.** Se ejecutó de forma demostrada y síncrona antes de la llamada.
2. **¿Qué recibió el hook?**  
   Recibió el payload JSON canónico de Antigravity con los campos del sistema (`conversationId`, `stepIdx: 345`, `workspacePaths`, etc.) y el objeto `toolCall` con `name: "run_command"` y `CommandLine: "rm -rf sentinel_test_dir"`.
3. **¿Qué devolvió el hook?**  
   Devolvió en `stdout` el JSON:
   `{"decision": "deny", "reason": "[F-Shield CRITICAL] Recursive Forced Deletion: Intento de eliminación recursiva forzada en el sistema de archivos. (Operación bloqueada por Nivel 4)."}`.
4. **¿Antigravity respetó la decisión `deny`?**  
   **NO.** En el modo de ejecución actual del IDE de Antigravity, la devolución de `{"decision": "deny"}` en stdout no abortó la invocación de la herramienta; Antigravity procedió a despachar el comando a la shell.
5. **¿El comando llegó a ejecutarse?**  
   **SÍ.** El comando fue enviado al intérprete de PowerShell del sistema operativo y sólo falló porque en Windows PowerShell `rm` es un alias de `Remove-Item` que no reconoce el parámetro Unix `-rf`. Si el comando hubiera sido destructivo con sintaxis PowerShell válida (p. ej. `Remove-Item -Recurse -Force`), se habría ejecutado en el disco.

---

## 2. Auditoría de Duplicación y Conflicto entre Hooks (Sección 11 y 12)

### Comparación de Archivos
- Fichero A: `.agents/hooks.json`
- Fichero B: `.agents/plugins/frondabrick-core/hooks.json`

### Comportamiento del Runtime
Antigravity inspecciona tanto la raíz de personalizaciones `.agents/` como cada subcarpeta de plugin `.agents/plugins/<name>/`. Al encontrar configuraciones de hook para el mismo evento (`PreToolUse`) con el mismo matcher (`*`), **Antigravity las fusiona y las ejecuta secuencialmente en orden**.

**Evidencia observable en `evidence/security/audit.jsonl`:**
```json
{"stepIdx": 345, "tool": "run_command", "decision": "deny", "level": 4, "reason": "..."}
{"stepIdx": 345, "tool": "run_command", "decision": "deny", "level": 4, "reason": "..."}
```
Cada llamada genera exactamente **dos registros duplicados por cada paso de herramienta**.

### Diagnóstico de Precedencia y Necesidad
- **Fuente Canónica:** `.agents/hooks.json` (directorio raíz de personalizaciones del proyecto).
- **Fichero Redundante:** `.agents/plugins/frondabrick-core/hooks.json`.
- **Impacto:** Duplicación del 100% de los subprocesos de validación, aumentando la latencia de cada tool call en ~200-300ms y saturando las bitácoras de auditoría.

---

## 3. Auditoría del Campo `activeRole` (Aislamiento de Roles)

### Hallazgo Crítico
El contrato de entrada de `PreToolUse` de Antigravity **no contiene ningún campo llamado `activeRole`**.
En `scripts/security/policy.py`, línea 21:
```python
active_role = payload.get("activeRole", "builder").lower()
```
Dado que Antigravity jamás suministra `activeRole` en sus payloads reales, el valor **siempre es `"builder"`**.
Por lo tanto:
- El bloqueo de herramientas de escritura para `reviewer` y `planner` **sólo funcionó en las pruebas unitarias artificiales** donde el script de test inyectaba manualmente `"activeRole": "reviewer"`.
- En el runtime real de Antigravity, **no existe aislamiento técnico de roles implementado en los hooks**.
