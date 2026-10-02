# Sistema de Memoria Persistente de Frondabrick

**Documento:** `docs/MEMORY.md`  
**Módulo Responsable:** F-Memory  

---

## 1. Propósito y Filosofía
F-Memory resuelve el problema del cold-start (arranque en frío) en sesiones continuadas de desarrollo, evitando al mismo tiempo el sobrecalentamiento del contexto (*context bloat*) y la contaminación por alucinaciones.

---

## 2. Jerarquía de Almacenamiento
- `memory/session/`: Bitácoras y eventos volátiles de la sesión de trabajo en curso.
- `memory/candidates/`: Observaciones preliminares con baja confianza (`confidence <= 0.5`).
- `memory/verified/`: Reglas y heurísticas consolidadas con alta confianza (`confidence >= 0.7`).
- `memory/anti-patterns/`: Prácticas defectuosas o dañinas documentadas para no volver a repetirlas.

---

## 3. Esquema Formal de 8 Campos
Todo registro de memoria persistente debe contener:
```json
{
  "id": "MEM-12D61D4A",
  "content": "Descripción concisa del patrón o lección aprendida",
  "origin": "Identificador de la tarea o prueba de origen",
  "created_at": "2026-10-02T20:30:00Z",
  "last_verified": "2026-10-02T20:45:00Z",
  "confidence": 0.75,
  "domain": "powershell",
  "status": "verified"
}
```

---

## 4. Regla Anti-Contaminación y Umbrales
- **Prohibido:** Convertir automáticamente una corrección aislada en regla permanente.
- **Observación Inicial:** Confianza inicial topada en 0.5.
- **Refuerzo:** Cada confirmación repetida eleva la confianza en pasos de 0.2 a 0.25.
- **Promoción:** Requiere explícitamente alcanzar o superar el umbral de `0.7`.
