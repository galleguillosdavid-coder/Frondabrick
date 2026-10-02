# Políticas de Seguridad de Frondabrick

**Documento:** `docs/SECURITY.md`  
**Módulo Responsable:** F-Shield  

---

## 1. Modelo de Amenazas
El arnés opera en un entorno donde un agente autónomo de IA posee acceso a la línea de comandos (`run_command`) y al sistema de archivos (`write_to_file`, `replace_file_content`). Las principales amenazas mitigadas son:
1. **Comandos Destructivos Accidentales o Inducidos:** Eliminación forzada de código o sistema (`rm -rf`, `del /s`, `format`).
2. **Destrucción de Historial o Datos:** Reseteos forzados de git (`git reset --hard`, `git push --force`) o borrado de bases de datos (`DROP TABLE`).
3. **Exposición de Credenciales:** Filtración de claves privadas (`BEGIN RSA PRIVATE KEY`), tokens API (`sk-...`, `ghp_...`) o archivos `.env`.
4. **Escalamiento de Privilegios:** Roles de auditoría o planificación modificando código de producción.

---

## 2. Los 5 Niveles de Defensa de F-Shield

| Nivel | Nombre | Decisión Hook | Acción Operativa |
| :---: | :--- | :---: | :--- |
| **1** | Detectar | `allow` | Registra el evento en `evidence/security/audit.jsonl` de forma transparente. |
| **2** | Advertir | `allow` | Emite un aviso explícito en el log o mensaje efímero advirtiendo del riesgo. |
| **3** | Solicitar Confirmación | `ask` / `force_ask` | Interrumpe la ejecución y traslada la decisión al desarrollador humano. |
| **4** | Bloquear | `deny` | Rechaza el comando o herramienta de inmediato explicando la regla vulnerada. |
| **5** | Modificar Parámetros | `allow` + `overwrite` | Muta los argumentos de la herramienta hacia una variante segura o acotada. |

---

## 3. Catálogo de Patrones Normativos (Sección 14)
- **SEC-001 (Eliminación Recursiva):** Bloquea `rm -rf`, `del /s`, etc. Exceptúa `node_modules` y `tmp/`.
- **SEC-002 (Formato de Almacenamiento):** Bloquea `format`, `fdisk`, particionamiento.
- **SEC-003 (DROP SQL):** Requiere confirmación (`ask`) ante eliminación de esquemas/tablas.
- **SEC-004 (Destrucción Git):** Bloquea `git reset --hard`, `git clean -fd`, `git push --force`.
- **SEC-005 (Llaves Privadas):** Bloquea escritura de claves RSA/OpenSSH.
- **SEC-006 (Tokens y Secretos):** Bloquea credenciales de OpenAI, GitHub, AWS.
- **SEC-007 (Archivos .env):** Exige confirmación para manipular archivos de entorno (exceptúa `.env.example`).
