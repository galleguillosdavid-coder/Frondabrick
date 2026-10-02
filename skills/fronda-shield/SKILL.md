---
name: fronda-shield
description: Supervisa y aplica los 5 niveles de defensa y políticas de seguridad ante comandos destructivos, filtración de credenciales y accesos no autorizados.
---

# Fronda Shield Skill

## PROPÓSITO
Proteger la integridad del sistema operativo, el repositorio y los secretos del proyecto mediante intercepción proactiva y aplicación de políticas de seguridad multinivel.

## CUÁNDO USAR
- Para verificar si una operación o comando planeado contiene riesgos destructivos.
- Para auditar el repositorio en busca de credenciales filtradas o variables de entorno expuestas.
- Para configurar o inspeccionar las reglas del hook `PreToolUse`.

## CUÁNDO NO USAR
- Para corregir errores de compilación o fallos de pruebas (usar F-Build-Resolver).
- Para diseñar planes de arquitectura de producto (usar F-Planner).

## PROCEDIMIENTO
1. Invocar el validador de seguridad pasando el comando o archivo a inspeccionar.
2. Evaluar el riesgo según la escala de 5 niveles (Detectar, Advertir, Solicitar confirmación, Bloquear, Modificar parámetros).
3. Si el nivel es 4 (Bloquear), detener la acción e informar la causa exacta.
4. Registrar la traza en la bitácora de auditoría de seguridad.

## REGLAS CRÍTICAS
- Prohibido omitir el bloqueo ante comandos destructivos de disco o eliminación forzada.
- Jamás registrar llaves privadas ni tokens reales en texto claro en logs de auditoría.
- Toda excepción debe contar con una justificación verificable.

## REFERENCIAS
- Niveles de seguridad: [levels.md](./references/levels.md)
- Catálogo de patrones: [patterns.md](./references/patterns.md)
