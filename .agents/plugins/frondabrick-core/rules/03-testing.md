# Frondabrick Core Rules — 03-testing

## 1. Obligatoriedad de Pruebas (No Test = No Finalizado)
Ningún componente, módulo, agente, script o regla se considerará finalizado sin una suite de pruebas reproducible que verifique su comportamiento frente a casos de éxito y casos límite.

## 2. Estados Formales Permitidos
Los resultados de ejecución y auditoría solo pueden calificarse con uno de los siguientes estados canónicos:
- **PASS:** La prueba se ejecutó y superó todas las aserciones con código de salida 0 y evidencia observable.
- **FAIL:** La prueba falló en una o más aserciones o produjo errores en runtime. Exige detención inmediata y corrección.
- **INCONCLUSIVE:** La prueba no pudo determinar el resultado debido a factores externos o precondiciones incompletas.
- **NOT_SUPPORTED:** La funcionalidad fue evaluada y se demostró que el entorno/antigravity no la soporta.

*Prohibición estricta:* Queda prohibido emitir calificaciones ambiguas como "parece funcionar", "debería andar" o "probablemente pase".

## 3. Criterios de Aceptación de Suite
- Pruebas deterministas sin efectos secundarios no controlados en el entorno de desarrollo.
- Cobertura de entradas válidas, entradas inválidas y ataques adversariales deliberados.
- Toda prueba debe generar o actualizar un informe de evidencia.
