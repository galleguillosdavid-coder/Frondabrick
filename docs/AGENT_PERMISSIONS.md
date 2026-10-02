# Matriz de Permisos de Agentes en Frondabrick

**Documento:** `docs/AGENT_PERMISSIONS.md`  
**Adaptación Técnica:** Mecanismos reales de Antigravity (Herramientas nativas + Hook `PreToolUse` de F-Shield)  

---

## 1. Adaptación a las Herramientas Reales de Antigravity

Antigravity no posee un selector nativo de permisos por archivo de agente. El aislamiento se logra mediante la intercepción programática de **F-Shield** en el evento `PreToolUse`, el cual evalúa el campo `activeRole` antes de autorizar la herramienta invocada:

- **Herramientas de Lectura (Read):** `view_file`.
- **Herramientas de Búsqueda (Search):** `list_dir`, `grep_search`.
- **Herramientas de Ejecución (Execute):** `run_command`, `manage_task`.
- **Herramientas de Escritura (Write):** `write_to_file`, `replace_file_content`, `multi_replace_file_content`.
- **Herramientas de Navegador (Browser):** `browser_subagent`.

---

## 2. Matriz de Autorización por Rol

| Rol / Agente | Read (`view_file`) | Search (`list/grep`) | Execute (`run_command`) | Write (`write/replace`) | Browser (`browser_subagent`) | Delete (`rm/del`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **F-Planner** | ✓ Autorizado | ✓ Autorizado | ⚠ Limitado (sólo tests/lectura) | ✗ Denegado (sólo planes en docs) | ✗ Denegado | ✗ Denegado |
| **F-Reviewer** | ✓ Autorizado | ✓ Autorizado | ✗ Denegado (auditoría pasiva) | ✗ Denegado | ✗ Denegado | ✗ Denegado |
| **F-Builder** | ✓ Autorizado | ✓ Autorizado | ✓ Autorizado | ✓ Autorizado | ✗ Denegado | ✗ Denegado (F-Shield) |
| **F-Shield** | ✓ Autorizado | ✓ Autorizado | ⚠ Sólo scripts de validación | ✗ Denegado | ✗ Denegado | ✗ Denegado |
| **F-Memory** | ✓ Autorizado | ✓ Autorizado | ⚠ Limitado | ⚠ Sólo `memory/` | ✗ Denegado | ✗ Denegado |
| **F-BuildResolver** | ✓ Autorizado | ✓ Autorizado | ✓ Autorizado (reproduce/rerun) | ✓ Autorizado (fix mínimo) | ✗ Denegado | ✗ Denegado |
| **F-BrowserQA** | ✓ Autorizado | ✓ Autorizado | ⚠ Local server dev | ⚠ Sólo `evidence/` | ✓ Autorizado | ✗ Denegado |

---

## 3. Mecanismo de Imposición (Enforcement)
1. **Gating Dinámico:** El hook `PreToolUse` consulta `ShieldPolicyEngine`.
2. **Denegación Temprana:** Si un rol no autorizado intenta invocar una herramienta fuera de su matriz, la ejecución se cancela inmediatamente devolviendo `{"decision": "deny", "reason": "..."}`.
3. **No Escalabilidad Silenciosa:** Todo intento de violación queda registrado en `evidence/security/audit.jsonl`.
