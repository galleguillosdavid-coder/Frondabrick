# Ciclo de Vida y Esquema de Memoria

### Los 8 Campos Obligatorios
1. `id`: Identificador único (prefijo `MEM-` o `ANTI-`).
2. `content`: Enunciado descriptivo de la lección o patrón.
3. `origin`: Origen o tarea donde se observó.
4. `created_at`: Marca temporal ISO 8601 UTC de creación.
5. `last_verified`: Marca temporal de la última comprobación exitosa.
6. `confidence`: Valor numérico flotante en el rango [0.0, 1.0].
7. `domain`: Dominio o tecnología (`python`, `git`, `security`, etc.).
8. `status`: Estado actual (`candidate`, `verified`, `anti-pattern`, `deprecated`).

### Umbrales de Promoción
- Candidato inicial: `confidence = 0.3` (tope 0.5)
- Incremento por refuerzo: `+0.2` a `+0.25`
- Umbral de promoción a verificado: `confidence >= 0.7`
