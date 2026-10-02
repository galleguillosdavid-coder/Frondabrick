# F-Planner: Matriz de Permisos

| Herramienta / Acción | Autorización | Propósito |
| :--- | :---: | :--- |
| `view_file` | **PERMITIDO** | Inspección de arquitectura existente |
| `list_dir` | **PERMITIDO** | Inspección de estructura del árbol de directorios |
| `grep_search` | **PERMITIDO** | Búsqueda de símbolos, clases y referencias |
| `write_to_file` (Planes/Docs) | **PERMITIDO** | Generación de planes en `docs/` o artefactos |
| `write_to_file` (Código fuente) | **BLOQUEADO** | Prohibido escribir código productivo |
| `replace_file_content` (Código) | **BLOQUEADO** | Prohibido modificar código de producción |
| `git commit` / `git push` | **BLOQUEADO** | Prohibido modificar historial |
