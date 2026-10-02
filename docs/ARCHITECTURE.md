# Arquitectura de Frondabrick

**Proyecto:** Frondabrick Engineering Harness for Antigravity  
**Versión:** 1.0.0  
**Estado:** OPERATIVO / VERIFICADO  

---

## 1. Visión General
Frondabrick es un arnés de ingeniería para agentes de programación que opera sobre la plataforma Google Antigravity. Proporciona una capa desacoplada de reglas, habilidades, roles de agentes, guardarraíles de seguridad, test harness, memoria persistente controlada y evidencia auditable.

```text
                  +------------------------------------------+
                  |         USUARIO / ANTIGRAVITY IDE        |
                  +------------------------------------------+
                                       |
                                       v
                  +------------------------------------------+
                  |                 F-FLEET                  |
                  |  Planner | Reviewer | Builder | Resolver |
                  +------------------------------------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
    +-------------------------+                 +-------------------------+
    |        F-SHIELD         |                 |        F-MEMORY         |
    |  PreToolUse Gatekeeper  |                 |  Observation -> Verify  |
    |  5 Defense Levels       |                 |  Anti-Pattern Catalog   |
    +-------------------------+                 +-------------------------+
                 |                                           |
                 v                                           v
    +-------------------------+                 +-------------------------+
    |     SISTEMA DE TEST     |                 |   SISTEMA DE EVIDENCIA  |
    |  13 Suites Automatizadas|                 |  Las 7 Preguntas        |
    |  No Test = No Terminado |                 |  4 Categorías Físicas   |
    +-------------------------+                 +-------------------------+
```

---

## 2. Componentes Fundamentales

### F-Core
Núcleo mínimo normativo alojado en `.agents/plugins/frondabrick-core/` y `.agents/rules/`. Define los principios rectores:
- **Realidad > Diseño:** Comprobación empírica en el workspace real.
- **Regla Anti-Alucinación:** Separación entre Hecho, Documentado, Inferido, Hipótesis y No Soportado.
- **Mínimo Privilegio:** Ningún agente posee permisos superiores a su rol estricto.
- **Workflow Estándar:** Inspeccionar -> Planificar -> Implementar -> Testear -> Auditar -> Documentar.

### F-Shield
Sistema de guardarraíles síncronos integrado mediante el hook `PreToolUse` de Antigravity (`hooks.json`). Opera en 5 niveles:
1. Detectar (Trazabilidad)
2. Advertir (Aviso efímero)
3. Solicitar Confirmación (`ask` / `force_ask`)
4. Bloquear (`deny` inmediato)
5. Modificar Parámetros (`overwrite` top-level)

### F-Fleet
Flota de 7 roles especializados coordinados por el orquestador:
- `F-Planner`: Descomposición en planes de 10 secciones sin escribir código de producción.
- `F-Reviewer`: Auditor técnico independiente en modo estricto READ ONLY.
- `F-Builder`: Implementación de código bajo la regla de cambio mínimo.
- `F-Shield`: Monitoreo y aplicación de políticas de seguridad.
- `F-BuildResolver`: Diagnóstico y resolución de errores mediante el ciclo de 7 pasos.
- `F-Memory`: Gestión de la persistencia contextual y prevención de anti-patrones.
- `F-BrowserQA`: Pruebas visuales y de interacción DOM en navegador (`browser_subagent`).

### F-Memory
Memoria persistente basada en acumulación de confianza (`confidence`):
- `session/` -> `candidates/` -> `verified/` -> `anti-patterns/`
- Umbral de promoción estricto (`confidence >= 0.7`). Prohíbe convertir correcciones aisladas en reglas permanentes.

### Sistema de Evidencia
Trazabilidad de cada acción significativa respondiendo a las 7 preguntas obligatorias:
1. ¿Qué se hizo?
2. ¿Por qué?
3. ¿Qué archivos cambió?
4. ¿Qué comando se ejecutó?
5. ¿Qué resultado produjo?
6. ¿Qué pruebas pasaron?
7. ¿Qué pruebas fallaron?

---

## 3. Principio de Cambio Mínimo y Dependencias
- Preferir 1 archivo frente a 15, preferir 10 líneas frente a 300.
- Uso exclusivo de librerías estándar en el arnés de soporte para no generar deuda técnica ni superficie de ataque innecesaria.
