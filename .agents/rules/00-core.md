# Frondabrick Core Rules — 00-core

## 1. Principio Supremo: Realidad > Diseño
Todo componente y flujo del arnés debe ejecutarse, observarse y validarse contra el entorno real de Antigravity antes de considerarse implementado. Nunca asumas capacidades sin verificación empírica.

## 2. Prohibición Terminante de Inventar Capacidades (Anti-Alucinación)
- No inventar APIs, herramientas, hooks, parámetros o eventos no existentes en Antigravity.
- Si una característica descrita en el diseño no está demostrada, debe registrarse bajo las siguientes categorías oficiales:
  - **HECHO:** Comprobado directamente en ejecución real.
  - **DOCUMENTADO:** Presente en la especificación oficial pero aún no probado.
  - **INFERIDO:** Deducido lógicamente de evidencia observable.
  - **HIPÓTESIS:** Propuesta conceptual no probada.
  - **NO SOPORTADO:** Confirmado que no funciona o no existe en Antigravity.

## 3. Mínimo Privilegio (Principio de Aislamiento)
- Ningún rol debe disponer de más permisos que los estrictamente necesarios para su función.
- Los roles de lectura (Reviewer, Planner) tienen prohibido invocar herramientas de mutación o escritura (`write_to_file`, `replace_file_content`, `multi_replace_file_content`).
- Cualquier escalamiento de privilegios debe ser explícito y trazable.

## 4. Evidencia Obligatoria
- Toda afirmación de éxito debe estar respaldada por evidencia observable (logs de ejecución, salidas de terminal, diffs de código, pruebas con código de retorno 0).
- Queda prohibido declarar `PASS`, `TERMINADO` o `ÉXITO` basado en intuiciones o asunciones.
