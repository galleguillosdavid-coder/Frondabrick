# Frondabrick Evidence System

Este directorio almacena las evidencias estructuradas y verificables de todas las operaciones realizadas en el arnés.

## Estructura
- `session/`: Registro cronológico y trazabilidad de acciones por sesión.
- `security/`: Trazas y eventos auditados por F-Shield (detecciones, bloqueos, advertencias).
- `tests/`: Resultados de ejecuciones de pruebas y suites automatizadas.
- `architecture/`: Registro de decisiones de arquitectura (ADRs) y validaciones estructurales.

## Las 7 Preguntas Obligatorias
Toda evidencia registrada debe responder de forma estricta a:
1. **¿Qué se hizo?** (`what`)
2. **¿Por qué?** (`why`)
3. **¿Qué archivos cambió?** (`files_changed`)
4. **¿Qué comando se ejecutó?** (`command_executed`)
5. **¿Qué resultado produjo?** (`result`)
6. **¿Qué pruebas pasaron?** (`tests_passed`)
7. **¿Qué pruebas fallaron?** (`tests_failed`)
