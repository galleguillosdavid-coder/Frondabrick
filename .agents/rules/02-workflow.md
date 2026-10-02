# Frondabrick Core Rules — 02-workflow

## Flujo Operativo Estándar
Todo cambio en el proyecto debe transitar obligatoriamente por el siguiente ciclo ordenado:

```text
INSPECCIONAR
     ↓
PLANIFICAR
     ↓
IMPLEMENTAR
     ↓
  TESTEAR
     ↓
  AUDITAR
     ↓
DOCUMENTAR
```

### 1. INSPECCIONAR
- Explorar el directorio y la arquitectura existente.
- Identificar dependencias, herramientas activas y estado de Git.
- No asumir el estado previo de los ficheros.

### 2. PLANIFICAR
- Desglosar el objetivo en tareas verificables.
- Identificar riesgos, dependencias y criterios de aceptación.
- Producir un plan explícito antes de escribir código.

### 3. IMPLEMENTAR
- Ejecutar cambios mínimos necesarios (regla del cambio mínimo: 1 fichero antes que 15, 10 líneas antes que 300).
- Mantener integridad estilística y preservar comentarios existentes.

### 4. TESTEAR
- Ejecutar pruebas automatizadas locales inmediatamente después de la implementación.
- Comprobar que los códigos de salida sean estrictamente 0.

### 5. AUDITAR
- Ejecutar revisión de código independiente (revisión de diffs, políticas de seguridad).
- Verificar que no se hayan introducido secretos, deuda técnica ni regresiones.

### 6. DOCUMENTAR
- Actualizar `docs/`, `PHASE_REPORT.md` o bitácoras de cambios (`CHANGELOG.md`).
- Registrar evidencias verificables con fecha y estado formal.
