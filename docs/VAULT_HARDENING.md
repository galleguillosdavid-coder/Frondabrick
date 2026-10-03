# Bóveda de Protección Física y Hardening (Fase 22)

**Documento:** `docs/VAULT_HARDENING.md`  
**Fase:** Fase 22 — Hardening de la Bóveda y Regresión Automática  
**Fecha:** 2026-10-02  
**Módulo Responsable:** `scripts/vault/verifier.py`  
**Suite de Pruebas:** `tests/vault/test_vault_hardening.py`  

---

## 1. Axioma de Autoridad y Alcance de la Protección

> [!IMPORTANT]
> **Regla Maestra del Sistema:**  
> F-Shield no es el mecanismo de prevención física. F-Shield detecta, clasifica y audita. La prevención física de los recursos protegidos depende de la política de acceso del sistema operativo. Las pruebas de canario verifican periódicamente que dicha frontera continúa existiendo.

### Alcance Riguroso de la Protección NTFS:
La operación de eliminación es rechazada por el mecanismo de control de acceso de Windows/NTFS para la identidad utilizada en la prueba (`DESKTOP-97NK4LA\Frondabrick`).  
La protección demostrada garantiza que **la identidad y contexto de ejecución del agente en este entorno no pueden eliminar el recurso protegido mediante comandos de terminal (`del`, `rmdir`, `Remove-Item -Force`)**.  
No se califica como "100% invulnerable contra cualquier actor", ya que procesos ejecutándose bajo otra identidad, cuentas con privilegios administrativos elevados, el usuario `SYSTEM` o modificaciones directas de ACL fuera del contexto del agente pertenecen a un dominio de privilegios superior no cubierto por este modelo de amenaza.

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

---

## 6. Fase 23 — Verificación de Deriva y Persistencia de la Bóveda

### EXP-23.1: Auditoría Detallada de Estado de ACL (Detector de Deriva)
El método `audit_vault_integrity` audita individualmente:
- `ACL_PRESENT`: PASS
- `DELETE_DENIED`: PASS
- `DELETE_CHILD_DENIED`: PASS
- `READ_ALLOWED`: PASS
- `EXPECTED_IDENTITY`: PASS
Si cualquiera de estas condiciones se degrada o falta la denegación esperada, el verificador emite de inmediato `protection_status: FAIL` y activa la bandera `drift_detected: True`.

### EXP-23.2: Persistencia entre Subprocesos Independientes
Demostración de que la protección no es un estado transitorio en memoria del proceso que la aplica:
1. Proceso A (Setup) crea el centinela y aplica la ACL de kernel.
2. Proceso A termina.
3. Se invoca un Proceso B completamente nuevo e independiente (subproceso aislado sin descriptores ni memoria compartida).
4. Proceso B verifica lectura -> PASS.
5. Proceso B intenta eliminar el centinela -> BLOCKED (`UnauthorizedAccessException`).
6. Proceso B verifica persistencia de hash SHA-256 -> PASS.
**Resultado:** `persistence: DEMONSTRATED`.

### EXP-23.3: Regresión Accidental Simulada (Tampering Test)
Una bóveda segura debe alertar cuando deja de estar protegida:
1. Se verifica la integridad inicial (`protection_status: PASS`).
2. Se simula una alteración accidental donde la ACL es removida deliberadamente.
3. El auditor detecta la pérdida de protección inmediatamente (`tamper_detected: PASS`, `drift_flagged: PASS`).
4. Se re-aplica la protección y se verifica la recuperación determinista (`recovery_verified: PASS`).
**Resultado:** `drift_detector: DEMONSTRATED`.

### EXP-23.4: Límites Formales de la Frontera de Seguridad
- **Identidad Normal (`Frondabrick`):**  
  Control de acceso efectivo verificado empíricamente contra comandos normales y forzados de shell.
- **Contexto Privilegiado (`Administrators` / `SYSTEM`):**  
  Declarado explícitamente fuera del modelo de amenaza del agente, reconociendo que procesos con privilegios de administrador o el subsistema del sistema operativo poseen autoridad superior de modificación de ACLs.

