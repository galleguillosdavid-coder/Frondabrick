---
name: fronda-build
description: Ejecuta compilaciones, verificación de dependencias, formateo y validación de tipos del proyecto de manera controlada.
---

# Fronda Build Skill

## PROPÓSITO
Orquestar las tareas de compilación, empaquetado, resolución de dependencias y linteo garantizando la reproducibilidad y estabilidad del build.

## CUÁNDO USAR
- Tras implementar cambios en el código para verificar que compila sin errores.
- Al añadir o actualizar dependencias necesarias del proyecto.
- Como paso previo a la ejecución de suites de prueba de integración.

## CUÁNDO NO USAR
- Para auditar seguridad y secretos (usar `fronda-shield`).
- Para redactar planes arquitectónicos (usar `fronda-planner`).

## PROCEDIMIENTO
1. Inspeccionar las dependencias actuales y verificar el gestor de paquetes del proyecto.
2. Ejecutar la compilación o type-checking en modo no destructivo.
3. Analizar la salida estándar y de error para detectar warnings o fallos de compilador.
4. Generar reporte con el resultado exacto y código de retorno.

## REGLAS CRÍTICAS
- Prohibido instalar paquetes globales o dependencias innecesarias sin justificación.
- Nunca ignorar advertencias críticas del compilador o linters.
- No alterar flags de compilación para ocultar errores reales de tipado o sintaxis.

## REFERENCIAS
- Protocolos de compilación: [build_protocols.md](../../../skills/fronda-build/references/build_protocols.md)
