# F-Reviewer: Matriz de Permisos y Control de Acceso

| Herramienta / Acción | Autorización | Mecanismo de Control |
| :--- | :---: | :--- |
| `view_file` | **PERMITIDO** | Permiso nativo de lectura |
| `list_dir` | **PERMITIDO** | Permiso nativo de navegación |
| `grep_search` | **PERMITIDO** | Búsqueda estática |
| `git status` / `git diff` | **PERMITIDO** | Inspección de control de versiones |
| `write_to_file` | **BLOQUEADO** | PreToolUse hook (F-Shield) emite `decision: "deny"` |
| `replace_file_content` | **BLOQUEADO** | PreToolUse hook (F-Shield) emite `decision: "deny"` |
| `multi_replace_file_content` | **BLOQUEADO** | PreToolUse hook (F-Shield) emite `decision: "deny"` |
| `git commit` | **BLOQUEADO** | Política de comandos; denegado para el rol reviewer |
| `git push` | **BLOQUEADO** | Política de comandos; denegado para el rol reviewer |
