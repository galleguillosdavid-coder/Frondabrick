---
name: fronda-tdd
description: Aplica la metodología rigurosa Test-Driven Development (Red-Green-Refactor) antes de modificar código de producción.
---

# Fronda TDD Skill

## PROPÓSITO
Garantizar que todo desarrollo nuevo o corrección de bugs esté guiado por pruebas automatizadas reproducibles escritas antes de la implementación.

## CUÁNDO USAR
- Al crear nuevas funcionalidades o módulos.
- Al reproducir y reparar un bug reportado (escribir primero la prueba que falla).
- Al realizar refactorizaciones estructurales de código.

## CUÁNDO NO USAR
- Al redactar documentos puramente conceptuales o de arquitectura sin código asociado.
- Al explorar APIs o dependencias en fase de experimentación exploratoria preliminar.

## PROCEDIMIENTO
1. **FASE ROJA (RED):** Escribir una prueba unitaria o de integración que describa el comportamiento esperado y ejecutarla para verificar que falla.
2. **FASE VERDE (GREEN):** Escribir el código mínimo indispensable para que la prueba pase con código de salida 0.
3. **FASE REFACTOR (REFACTOR):** Limpiar y optimizar el código manteniendo las pruebas en verde en todo momento.

## REGLAS CRÍTICAS
- Prohibido escribir código de producción sin una prueba previa que justifique su existencia.
- Jamás alterar las aserciones de una prueba únicamente para forzar un resultado PASS.
- Toda prueba debe ser determinista e independiente del orden de ejecución.

## REFERENCIAS
- Protocolo Red-Green-Refactor: [red_green_refactor.md](./references/red_green_refactor.md)
