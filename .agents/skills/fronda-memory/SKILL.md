---
name: fronda-memory
description: Administra el almacenamiento persistente de patrones, aprendizaje acumulado y prevención de anti-patrones bajo el esquema de 8 campos.
---

# Fronda Memory Skill

## PROPÓSITO
Permitir al arnés recordar decisiones técnicas, preferencias del desarrollador y soluciones validadas a través de sesiones de trabajo, evitando la pérdida de contexto y el cold-start.

## CUÁNDO USAR
- Al finalizar una sesión o hito importante para consolidar observaciones.
- Al identificar un patrón recurrente verificado mediante pruebas.
- Al detectar un anti-patrón o práctica defectuosa para prevenir su reaparición.

## CUÁNDO NO USAR
- Para persistir código de producción en texto plano (el código reside en el repositorio).
- Para guardar información efímera de una sola ejecución sin valor acumulativo.

## PROCEDIMIENTO
1. Registrar la observación candidata con confianza inicial acotada (`initial_confidence <= 0.5`).
2. Al observar repeticiones confirmadas, reforzar la puntuación de confianza.
3. Si supera el umbral de confianza (`>= 0.7`), promover a memoria verificada activa.
4. Si se confirma una práctica dañina, catalogarla en el registro de anti-patrones.

## REGLAS CRÍTICAS
- Prohibido convertir una observación aislada en regla permanente de forma automática.
- Cumplimiento estricto del esquema de 8 campos en todo registro de memoria.
- Jamás almacenar contraseñas, secretos ni datos personales sensibles en memoria.

## REFERENCIAS
- Ciclo de vida y esquema de memoria: [memory_lifecycle.md](../../../skills/fronda-memory/references/memory_lifecycle.md)
