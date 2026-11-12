# Historia 11c: tres casos que se escapaban de «si no se entiende, nunca comprobado»

**Estado: terminada (2026-11-10).**

1. **Claves repetidas en `opencode.json(c)`**: cada lector se queda con una (la última o la primera), así que el archivo no tiene un único significado. Ahora `parsear_jsonc(..., rechazar_repetidas=True)` lo rechaza: aviso `configuracion_no_interpretable`, nivel de opencode nunca «comprobado». Vale para una clave repetida en cualquier objeto del archivo; el mismo nombre en objetos distintos no cuenta.
2. **Patrones `Read` con `./` repetido o `..`** (`Read(././.env)`, `Read(sub/../.env)`): no tienen un significado documentado. Son «indeterminables» (como `[`, `{`, `!`): el nivel baja a potencial y se avisa. Siguen valiendo `./x`, `x`, `.` y `./`.
3. **`.claude` (u `.opencode`) que es un archivo**: antes se leía como «no hay configuración» y salía «comprobado». Ahora `carpeta_que_es_archivo` lo detecta y se avisa (`configuracion_no_interpretable` sobre esa ruta); vale también para la carpeta personal.

Pruebas: `tests/test_correcciones_11c.py` (27), con los casos de control (formas válidas y carpeta inexistente siguen igual). Pendiente: claves repetidas en `settings.json` de Claude Code (no pedido).
