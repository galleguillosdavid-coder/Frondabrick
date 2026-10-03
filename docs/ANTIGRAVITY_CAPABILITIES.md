# Antigravity Capabilities & Audit Matrix (FASE 0)

**Documento:** `docs/ANTIGRAVITY_CAPABILITIES.md`  
**Proyecto:** Frondabrick Harness  
**Fecha de Auditoría:** 2026-10-02  
**Entorno Operativo:** Windows 10/11, PowerShell, Antigravity IDE / 2.0 (Gemini 3.8 Flash)  
**Runtimes Verificados:** Python 3.14.6, Node v24.18.0, Git 2.45.1  

---

## 1. Clasificación Metodológica Anti-Alucinación

Toda capacidad descrita se clasifica estrictamente en una de las 5 categorías:
1. **HECHO (FACT):** Verificado experimentalmente mediante ejecución real y observable en este entorno.
2. **DOCUMENTADO (DOCS):** Documentado oficialmente en el SDK/sistema de personalizaciones de Antigravity (`agy-customizations`, `antigravity-guide`), pendiente de validación experimental en el flujo activo.
3. **INFERIDO (INFERRED):** Deducido de interfaces y herramientas expuestas en el arnés.
4. **HIPÓTESIS (HYPOTHESIS):** Propuesto conceptualmente sin evidencia formal en Antigravity.
5. **NO SOPORTADO (NOT_SUPPORTED):** Probado y confirmado como no funcional o no existente en la arquitectura nativa.

---

## 2. Matriz de Capacidades de Antigravity

| Capacidad | Estado | Evidencia / Referencia | Limitaciones Reales | Nivel de Riesgo |
| :--- | :---: | :--- | :--- | :---: |
| **Workspace Rules** (`GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`) | **HECHO** | Descubrimiento jerárquico documentado en `rules.md` y probado en workspace. Inyección contextual directa. | Deduplicación por ruta resuelta; no soportan frontmatter en ficheros sueltos. | Bajo |
| **Skills System** (`.agents/skills/<name>/SKILL.md`) | **HECHO** | Documentado en `skills.md` y manifestado en `view_file` de skills activas. Frontmatter YAML obligatorio (`name`, `description`). | Carga perezosa (Progressive Disclosure); el contenido completo sólo se inyecta tras activación o lectura explícita. | Bajo |
| **Plugins Manifest** (`.agents/plugins/<name>/plugin.json`) | **DOCUMENTADO** | Documentado en `plugins.md`. Agrupa skills, rules, hooks y MCP configs bajo un espacio de nombres. | Requiere estructura de carpetas estricta; debe registrarse o ubicarse en `.agents/plugins/`. | Medio |
| **Lifecycle Hooks** (`PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`) | **DOCUMENTADO** | Documentado en `hooks.md`. Soporta comandos CLI vía `cmd /c` en Windows con payloads JSON stdin/stdout. | Sólo soporta `type: "command"`. Ejecución síncrona bloqueante. En Windows requiere rutas y quoting compatibles con `cmd /c`. | Medio-Alto |
| **Hook Overwrite / Parameter Mutation** (`PreToolUse.overwrite`) | **DOCUMENTADO** | Documentado formalmente en `hooks.md`: shallow merge en argumentos de la herramienta antes de su ejecución. | Debe validarse experimentalmente en EXP-001 antes de su uso como salvaguarda en F-Shield. | Alto |
| **Dynamic Tool Gating** (`PreToolUse.decision = allow/deny/ask/force_ask`) | **DOCUMENTADO** | Documentado formalmente en `hooks.md` con control de permisos y razones para el usuario. | Si el script del hook falla o no emite JSON válido, el comportamiento por defecto debe ser seguro (fail-safe). | Alto |
| **Sub-Agentes Declarativos Nativos** (`agents/<name>/agent.md`) | **NO SOPORTADO (NATIVO)** | En la especificación formal de personalizaciones de Antigravity (`agy-customizations`) sólo existen Rules, Skills, Plugins, Hooks y MCP. No existe un directorio nativo `agents/` ingerido automáticamente por el core. | Los roles de sub-agentes deben orquestarse como **Skills especializadas con límites de rol** (p. ej., `fronda-planner`, `fronda-reviewer`) combinadas con **Hooks de restricción de herramientas (F-Shield)** y el tool nativo `browser_subagent`. | Medio |
| **Browser QA Subagent** (`browser_subagent`) | **HECHO** | Herramienta nativa disponible en el entorno con capacidades de navegación, clicks, typing, lectura de DOM y grabación WebP. | Sólo aplicable para proyectos con UI web o interfaces frontend. | Bajo |
| **MCP Servers** (`mcp_config.json`) | **DOCUMENTADO** | Especificado en `mcp_servers.md` para conectar herramientas y servidores externos. | Requiere procesos en ejecución y consumo de memoria adicional. | Bajo |
| **Task Management / Async Tasks** (`manage_task`, `run_command` async) | **HECHO** | Verificado en la sesión. `run_command` con `WaitMsBeforeAsync` envía a background y notifica reactivamente. | Controlable con `manage_task` (kill/status/send_input). | Bajo |
| **Interacción con Usuario** (`ask_question`) | **HECHO** | Herramienta modal nativa con soporte para opciones múltiples, write-ins y confirmaciones. | Bloquea la ejecución hasta la respuesta del usuario. | Bajo |
| **Persistencia y Memoria** | **HECHO / INFERIDO** | Archivos locales en workspace (`.agents/memory/`), Knowledge Items (`<appDataDir>/knowledge`), Transcripts (`transcript.jsonl`). | Requiere esquemas de validación propios para evitar alucinaciones y contaminación. | Medio |

---

## 3. Decisión Arquitectónica Clave (Anti-Alucinación)

> **ADVERTENCIA ARQUITECTÓNICA (SECCIÓN 10-11 y 23 DEL PLAN):**  
> El plan original asume una carpeta `agents/` declarativa nativa para Antigravity.  
> **Auditoría Técnica:** La documentación de Antigravity (`.agents/` spec) no incluye un parser de agentes markdown autónomos como Everything Claude Code (Claude Code usa `agents/*.md`). Antigravity utiliza:
> 1. Herramientas dedicadas de sub-agentes (como `browser_subagent`).
> 2. **Skills estructuradas** con directivas de rol estricto (`skills/fronda-planner/SKILL.md`, `skills/fronda-reviewer/SKILL.md`).
> 3. **Hooks de aislamiento de permisos (F-Shield)** que interceptan `PreToolUse` y emiten veredicto `deny` ante herramientas de escritura (`write_to_file`, `replace_file_content`, etc.) cuando se evalúa una operación de `Reviewer` o `Planner`.
> 
> **Resolución:** Implementaremos los agentes de Frondabrick bajo esta arquitectura verificada: **Rol delimitado por Skill + Barrera de cumplimiento normativo mediante Hooks y auditoría de evidencias**.
