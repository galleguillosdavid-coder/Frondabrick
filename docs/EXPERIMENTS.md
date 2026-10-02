# Registro de Experimentos de Frondabrick

**Documento:** `docs/EXPERIMENTS.md`  

---

## 1. Metodología de Experimentación
Todo experimento debe contar con la estructura física:
```text
experiments/EXP-XXX/
├── README.md
├── input/
├── output/
├── evidence/
└── result.md
```
Estados válidos de dictamen: `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_SUPPORTED`.

---

## 2. Índice de Experimentos Realizados

### EXP-001: Validación de Capacidades y Contratos de Antigravity
- **Fase:** Fase 0 (Auditoría de Antigravity)
- **Fecha:** 2026-10-02
- **Dictamen:** **PASS**
- **Resultados:**
  - Manifiesto de plugin (`plugin.json`): Validado con campo obligatorio `name`.
  - Skills frontmatter YAML (`name`, `description`): Validado.
  - Hook `PreToolUse`: Verificado contrato stdin/stdout JSON con decisiones `allow` y `deny`.
  - Mutación de parámetros: Verificado contrato `overwrite` top-level.
  - Aislamiento de rol: Intento de escritura en rol Reviewer bloqueado exitosamente.
- **Ruta:** [`experiments/EXP-001/`](../experiments/EXP-001/)
