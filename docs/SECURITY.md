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
- **SEC-001 (Eliminación Recursiva):** Bloquea `rm -rf`, `del /s`, `del /q /s`, `Remove-Item -r`, `rmdir /s`. Exceptúa `node_modules` y `tmp/`.
- **SEC-002 (Formato de Almacenamiento):** Bloquea `format`, `fdisk`, particionamiento.
- **SEC-003 (DROP SQL):** Requiere confirmación (`ask`) ante eliminación de esquemas/tablas.
- **SEC-004 (Destrucción Git):** Bloquea `git reset --hard`, `git clean -fd`, `git push --force`.
- **SEC-005 (Llaves Privadas):** Bloquea escritura de claves RSA/OpenSSH.
- **SEC-006 (Tokens y Secretos):** Bloquea credenciales de OpenAI, GitHub, AWS.
- **SEC-007 (Archivos .env):** Exige confirmación para manipular archivos de entorno (exceptúa `.env.example`).
- **SEC-008 (PowerShell Encoded Command):** Exige confirmación (`ask`) para comandos invocados con payload base64 codificado (`-e`, `-enc`, `-encodedcommand`).

---

## 4. Definición Realista de DENY y Limitaciones de Runtime

> [!IMPORTANT]
> **F-Shield es un validador normativo y compuerta de auditoría, NO un sandbox de kernel.**

1. **Significado Operacional de `DENY`:**
   - En el arnés de Frondabrick, una decisión `deny` representa un **Veredicto Normativo de Infracción y Rechazo de Política**.
   - Queda formalmente registrado en la bitácora de auditoría (`evidence/security/audit.jsonl`) y expuesto en la salida del hook `PreToolUse`.
   - Si el runtime del cliente/IDE que invoca las herramientas no intercepta ni anula coercitivamente el proceso hijo del sistema operativo, el comando puede llegar a ejecutarse a nivel de shell. Por lo tanto, `deny` **no debe considerarse una garantía de aislamiento a nivel de sistema operativo ni un sandbox de ejecución**.

2. **Aislamiento de Roles:**
   - La restricción de herramientas para roles de lectura (`reviewer`, `planner`) opera a nivel de política de diseño y verificación de arnés. Antigravity IDE no proporciona de forma nativa la propiedad `activeRole` en el payload del hook; la separación de permisos se rige por contratos de orquestación y prompts de rol.

3. **Manejo de Falsos Positivos:**
   - Comandos de inspección pasiva y búsqueda de texto (`git grep`, `rg`, `grep`, `findstr`, `echo`, `cat`, `type`, `Select-String`) que contienen cadenas o nombres de patrones peligrosos (ej. buscar ocurrencias de `DROP TABLE` en el código) son expresamente clasificados como seguros y excluidos de bloqueo, preservando la operatividad del desarrollador en el flujo de inspección.
