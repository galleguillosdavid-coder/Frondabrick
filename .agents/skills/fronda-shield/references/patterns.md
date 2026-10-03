# Catálogo de Patrones de Seguridad F-Shield

| ID | Patrón Regex | Riesgo | Acción | Nivel | Excepción Autorizada |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **SEC-001** | `\b(rm\s+-[rRfF]{1,3}\b\|del\s+/[sS]\b)` | CRÍTICO | BLOCK | 4 | Limpieza en carpetas `tmp/`, `node_modules` |
| **SEC-002** | `\bformat\s+[a-zA-Z]:` | CRÍTICO | BLOCK | 4 | Ninguna |
| **SEC-003** | `\bDROP\s+(?:DATABASE\|SCHEMA\|TABLE)\b` | ALTO | ASK | 3 | Tablas con prefijo `temp_` o `test_` |
| **SEC-004** | `\bgit\s+(?:reset\s+--hard\|clean\s+-[fF]\|push\s+.*--force)` | ALTO | BLOCK | 4 | Ninguna |
| **SEC-005** | `-----BEGIN\s+.*PRIVATE\s+KEY-----` | CRÍTICO | BLOCK | 4 | Ninguna |
| **SEC-006** | `\b(?:sk-[a-zA-Z0-9]{20,}\|ghp_[a-zA-Z0-9]{30,})\b` | ALTO | BLOCK | 4 | Tokens de prueba mock en suites de test |
| **SEC-007** | `(?:^\|[\\/])\.env(?:\..*)?$` | MEDIO | ASK | 3 | Ficheros `.env.example` |
