# Bóveda de Protección Física y Hardening (Fase 22)

**Documento:** `docs/VAULT_HARDENING.md`  
**Fase:** Fase 22 — Hardening de la Bóveda y Regresión Automática  
**Fecha:** 2026-10-02  
**Módulo Responsable:** `scripts/vault/verifier.py`  
**Suite de Pruebas:** `tests/vault/test_vault_hardening.py`  

---

## 1. Axioma de Autoridad y Alcance de la Protección

> [!IMPORTANT]
> **Axioma del Sistema:**
> F-Shield no promete impedir físicamente una operación: **detecta, clasifica, alerta y audita**.
> La autoridad física pertenece a la frontera del sistema operativo que realmente puede impedir la destrucción (Windows NTFS en el contexto de ejecución evaluado).

### Alcance Riguroso de la Protección NTFS:
La protección demostrada garantiza que **la identidad y contexto de ejecución del agente en este entorno no pueden eliminar el recurso protegido mediante comandos de terminal (`del`, `rmdir`, `Remove-Item -Force`)**.  
No se califica como "100% invulnerable", ya que procesos con privilegios administrativos elevados, el usuario `SYSTEM` o modificaciones directas de ACL fuera del contexto del agente pertenecen a un dominio de privilegios superior.

---

## 2. EXP-22.1: Inventario de Recursos

| Clasificación | Recursos | Política de Acceso | Justificación Operativa |
| :--- | :--- | :---: | :--- |
| **PROTECTED (Bóveda)** | `chat gpt`, `gen.md`, artefactos de calibración | **READ-ONLY / NO-DELETE** | Documentos fundacionales y especificaciones que nunca deben ser destruidos ni alterados por scripts automáticos. |
| **PROTECTED (Remoto)** | Historial Git (`origin/main`) | **DISTRIBUIDO / INMUTABLE** | `.git/` local requiere creación y borrado de archivos efímeros de bloqueo (`.git/index.lock`, `COMMIT_EDITMSG`) durante cada commit normal; por ende, su resiliencia definitiva reside en el repositorio remoto sincronizado. |
| **MUTABLE (Workspace)**| `src/`, `tests/`, `scripts/`, `docs/`, `build/`, `tmp/` | **FULL CONTROL (R/W/D)** | Espacio de pair-programming donde el agente debe refactorizar, compilar, ejecutar pruebas TDD y limpiar temporales con 100% de autonomía. |

---

## 3. EXP-22.2 & EXP-22.3: Verificador y Prueba de Regresión de Canario

El módulo `scripts/vault/verifier.py` automatiza la verificación periódica de la frontera física sin intervención manual:

```text
                     EJECUCIÓN DEL CANARIO
                               │
            1. Crear centinela con payload SHA-256
                               │
            2. Aplicar política NTFS:
               icacls <dir> /deny %USERNAME%:(OI)(CI)(DE,DC)
                               │
            3. Verificar lectura del centinela
                               │
            4. Ataque: cmd /c del /f /q <canary.txt>
               -> Esperar: Acceso denegado
                               │
            5. Ataque: powershell Remove-Item -Recurse -Force
               -> Esperar: UnauthorizedAccessException (Error)
                               │
            6. Verificar supervivencia del directorio y archivo
                               │
            7. Verificar coincidencia byte a byte de SHA-256
                               │
            8. Desactivar ACL y limpieza segura
```

### Reporte Automatizado de Verificación:

```text
VAULT TEST REPORT
────────────────────────────────────────────
ACL                      PASS
READ                     PASS
DELETE                   BLOCKED
DELETE_CHILD             BLOCKED
CANARY_EXISTS            PASS
HASH (SHA-256)           PASS
────────────────────────────────────────────
ENFORCEMENT              DEMONSTRATED
```

---

## 4. EXP-22.4: Demostración de Autonomía de Desarrollo

Simultáneamente, la suite comprueba que el resto del workspace no sufre degradación:

```text
AUTONOMY TEST REPORT
────────────────────────────────────────────
CREATE (mutable file)    PASS
EDIT (content update)    PASS
EXECUTE (python runtime) PASS
DELETE (cleanup)         PASS
────────────────────────────────────────────
AUTONOMY                 DEMONSTRATED
```

---

## 5. Integración en el Arnés Maestro

La suite de pruebas `tests/vault/test_vault_hardening.py` está incorporada en el runner unificado:
- **14/14 Suites Aprobadas (PASS)** en `python tests/run_all.py`.
- **10/10 Comprobaciones (PASS)** en `python frondabrick.py doctor`.
