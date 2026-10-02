# Protocolos de Compilación y Validación

### Verificación de Dependencias
- Comprueba la existencia de lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`).
- Utiliza siempre comandos reproducibles y con flags de verificación limpia (`npm ci` en lugar de `npm i` en CI).

### Limpieza de Artefactos
- Antes de declarar un fallo persistente de compilación, limpia las cachés locales autorizadas (`tmp/`, `.pytest_cache/`).
