# Frondabrick Core Rules — 01-safety

## 1. Operaciones Destructivas Prohibidas
Quedan categorizadas como operaciones de alto riesgo sujetas a bloqueo o confirmación obligatoria:
- Eliminación recursiva o forzada: `rm -rf`, `rmdir /s`, `del /s`, `Remove-Item -Recurse -Force`.
- Comandos destructivos de disco: `format`, `fdisk`, particionamiento.
- Destrucción de bases de datos: `DROP DATABASE`, `DROP TABLE`, `DROP SCHEMA`, `TRUNCATE` sin cláusulas de seguridad.
- Reseteos destructivos de VCS: `git reset --hard`, `git clean -fd`, `git push --force`.

## 2. Protección de Secretos y Credenciales
- No escribir, imprimir en stdout ni registrar en evidencia credenciales reales, tales como:
  - Tokens de API (OpenAI, Anthropic, GitHub, Google API Keys).
  - Llaves privadas SSH o certificados RSA (`BEGIN RSA PRIVATE KEY`).
  - Variables de entorno sensibles contenidas en ficheros `.env`, `credentials.json`, `id_rsa`.
- Al generar salidas o documentación, ofuscar o enmascarar automáticamente cualquier secreto detectado.

## 3. Integridad y Protección de Archivos
- No sobrescribir ficheros de código sin haberlos inspeccionado previamente (`view_file`).
- No eliminar archivos sin confirmación explícita o justificación documentada.
- Aplicar la regla de cambio mínimo: preferir ediciones acotadas y quirúrgicas antes que reemplazos masivos de código.

## 4. Estrategia de Rollback y Recuperación
- Toda modificación crítica en el repositorio debe estar protegida mediante versionado Git (`git status`, `git diff`) o respaldos temporales.
- Si una prueba o comando falla, el sistema debe ser capaz de revertir al último estado limpio y reproducible.
