# Frondabrick F-Memory System

Este módulo gestiona la memoria persistente del agente evitando el problema del arranque en frío (cold-start) y la contaminación del contexto (context bloat).

## Estructura de Memoria
- `session/`: Observaciones transitorias registradas durante la sesión activa.
- `candidates/`: Patrones candidatos observados repetidamente, pendientes de validación.
- `verified/`: Reglas y patrones validados y consolidados con alta puntuación de confianza (`confidence >= 0.7`).
- `anti-patterns/`: Patrones dañinos o prácticas desaconsejadas identificadas empíricamente.

## Ciclo de Promoción de Memoria
```text
SESIÓN (Observación inicial, confidence=0.3)
   ↓
CANDIDATO (Repetición observada, confidence incrementa)
   ↓
VALIDACIÓN (Confirmación experimental)
   ↓
VERIFICADO (Promoción oficial a memoria persistente activa)
```

## Regla Anti-Contaminación
Queda terminantemente prohibido convertir de forma automática una corrección aislada en una regla permanente. Toda memoria debe acumular confianza verificable.
