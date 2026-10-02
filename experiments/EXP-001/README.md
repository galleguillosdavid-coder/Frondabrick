# Experimento EXP-001: Validación de Capacidades y Contratos de Antigravity

**Identificador:** EXP-001  
**Fase:** Fase 0 — Auditoría de Antigravity  
**Fecha:** 2026-10-02  
**Responsable:** Ingeniero Principal de Implementación de Frondabrick  

---

## 1. Propósito

Validar de forma experimental y verificable los mecanismos fundamentales sobre los que se construirá Frondabrick:
1. **Reglas (Rules):** Estructura jerárquica y formato Markdown sin frontmatter.
2. **Habilidades (Skills):** Estructura de directorio, frontmatter YAML obligatorio (`name`, `description`), convención de progressive disclosure.
3. **Plugins:** Formato del manifiesto `plugin.json` y estructura de empaquetado.
4. **Lifecycle Hooks & Tool Gating:**
   - Contrato stdin/stdout JSON de `PreToolUse`.
   - Lógica de decisión (`deny`, `allow`, `ask`, `force_ask`).
   - Mecanismo de modificación de parámetros (`overwrite`).
   - Aislamiento de permisos de agentes (bloqueo de herramientas de escritura para roles Reviewer y Planner).
5. **Runtime de Ejecución en Windows:** Verificación de invocación mediante Python y PowerShell.

---

## 2. Entradas (`input/`)

- `input/mock_pretooluse_dangerous.json`: Carga de prueba de un comando destructivo (`rm -rf /`).
- `input/mock_pretooluse_reviewer_write.json`: Carga de prueba donde un rol de lectura intenta invocar `write_to_file`.
- `input/mock_pretooluse_safe.json`: Carga de prueba para comando seguro (`git status`).
- `input/mock_plugin_manifest.json`: Manifiesto de plugin candidato.
- `input/mock_skill.md`: Archivo de skill candidato para validar frontmatter YAML.

---

## 3. Procedimiento de Prueba

Ejecutar el validador del experimento: `python experiments/EXP-001/harness_validator.py`.
El validador:
1. Evalúa el parser de frontmatter YAML para Skills.
2. Evalúa la estructura del manifiesto de Plugin.
3. Simula la ejecución de un hook `PreToolUse` contra las entradas destructivas, de rol y seguras.
4. Genera los resultados en `output/` y la evidencia en `evidence/`.
5. Emite un dictamen formal con estados válidos: `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_SUPPORTED`.

---

## 4. Criterio de Éxito

- Todos los contratos de datos coinciden con la especificación de `agy-customizations`.
- Las decisiones de seguridad bloquean comandos destructivos con `decision: "deny"`.
- Los intentos de escritura bajo rol de solo lectura son bloqueados.
- Las salidas se guardan con trazabilidad completa.
