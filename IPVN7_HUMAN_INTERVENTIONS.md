# IPVN7 — REGISTRO PERSISTENTE DE INTERVENCIONES HUMANAS

**Documento:** `IPVN7_HUMAN_INTERVENTIONS.md`  
**Estado:** REGISTRO ACUMULATIVO VIVO  
**Regla:** Nunca eliminar registros históricos. Cada nuevo bloqueo se agrega cronológicamente como una nueva entrada.

---

## 1. Principio Operativo

La autonomía de IPVN7 no se detiene globalmente porque una tarea particular requiera obligatoriamente intervención humana.

Un bloqueo humano afecta únicamente a la tarea que depende de dicha intervención, no al ciclo autónomo completo:

> **Si una tarea requiere intervención humana obligatoria, se documenta persistentemente el bloqueo y sus alternativas, se marca como `PENDIENTE_HUMANO`, y el sistema continúa inmediatamente con la siguiente tarea autónoma prioritaria que pueda ejecutarse sin dicha intervención.**

---

## 2. Registro Acumulativo de Intervenciones

*(Actualmente no existen bloqueos activos de tipo `PENDIENTE_HUMANO`. Todas las tareas en curso, incluyendo `EXP-IPVN7-09: Re-claveo Transparente en Vuelo`, son 100% ejecutables de forma autónoma en el entorno de desarrollo y laboratorio).*

---

### Formato Obligatorio para Futuras Entradas

```text
## [FECHA] — [CICLO / EXPERIMENTO]

Estado: PENDIENTE_HUMANO

Tarea bloqueada:
[identificación breve]

Motivo:
[explicación concreta y breve de por qué la tarea no puede continuar autónomamente]

Intervención requerida:
[acción específica que debe realizar una persona]

Alternativas para continuar:
- [alternativa 1]
- [alternativa 2]
- [alternativa 3, si existe]

Impacto:
[qué queda pendiente o qué capacidad no puede demostrarse mientras no se resuelva]

Dependencias:
[qué tareas dependen de esta intervención, si corresponde]
```
