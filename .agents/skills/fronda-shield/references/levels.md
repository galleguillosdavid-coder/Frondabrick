# Niveles de Protección F-Shield

### Nivel 1: Detectar
Registra eventos y comandos en la bitácora de auditoría sin interrumpir el flujo. Permite trazar la actividad del agente.

### Nivel 2: Advertir
Emite una advertencia visual al desarrollador y al agente en el mensaje efímero, señalando un posible riesgo sin bloquear la ejecución.

### Nivel 3: Solicitar Confirmación (`ask` / `force_ask`)
Detiene la ejecución y exige autorización explícita del usuario cuando una operación roza recursos sensibles (p. ej. `.env`, eliminación de tablas temporales).

### Nivel 4: Bloquear (`deny`)
Interrumpe de inmediato la ejecución devolviendo un error controlado y explicando el motivo de seguridad. Aplicado ante comandos destructivos (`rm -rf`, format, hard reset) y filtración de secretos.

### Nivel 5: Modificar Parámetros (`overwrite`)
Reescribe top-level los argumentos de la herramienta antes de su ejecución para neutralizar el riesgo sin romper la tarea (p. ej. forzar un flag de dry-run o acotar el alcance).
