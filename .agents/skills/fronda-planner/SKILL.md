---
name: fronda-planner
description: Estructura planes técnicos de ingeniería con 10 secciones obligatorias antes de realizar modificaciones en el código. No programa código fuente.
---

# Fronda Planner Skill

## PROPÓSITO
Descomponer requerimientos complejos y definir una hoja de ruta técnica precisa, verificable y con estrategia de reversión antes de cualquier desarrollo.

## CUÁNDO USAR
- Antes de comenzar tareas que impliquen cambios en múltiples archivos o dependencias.
- Ante nuevos requerimientos que exijan arquitectura, diseño de datos o cambios estructurales.

## CUÁNDO NO USAR
- Para escribir código productivo (usar el rol Builder).
- Para correcciones mínimas triviales (como un typo evidente de 1 línea).

## PROCEDIMIENTO
1. Inspeccionar el workspace y analizar las fuentes existentes con `view_file` y `grep_search`.
2. Identificar el alcance exacto y definir explícitamente el no-alcance para evitar sobre-ingeniería.
3. Redactar el plan siguiendo rigurosamente las 10 secciones de la plantilla oficial.
4. Validar el plan antes de delegar la ejecución a la fase de construcción.

## REGLAS CRÍTICAS
- F-Planner tiene terminantemente prohibido escribir o modificar código de producción.
- Es obligatorio incluir siempre las 10 secciones estándar (Objetivo, Alcance, No-Alcance, Archivos, Dependencias, Riesgos, Plan, Tests, Criterios de Aceptación, Rollback).

## REFERENCIAS
- Plantilla obligatoria: [PLAN_TEMPLATE.md](../../agents/planner/PLAN_TEMPLATE.md)
- Definición de rol: [ROLE.md](../../agents/planner/ROLE.md)
