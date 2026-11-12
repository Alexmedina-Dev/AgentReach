# Historia 22: permiso de lectura, resumen corto y reglas de la terminal

**Estado: terminada (2026-11-10).** Reemplaza la pregunta de la 21 (solo carpeta personal y raíz) por el flujo validado por Alex.

## Flujo
1. Abrir la terminal, entrar al proyecto, `agentreach` (sin ruta revisa la carpeta actual; con ruta, esa).
2. **Sin terminal interactiva (entrada y salida) no lee nada**: error, código 2. No existe `--permitir` ni nada que responda por la persona.
3. Banner mediano con aire (tres líneas en blanco antes y después) y qué es AgentReach, qué hace y qué no hace.
4. **Permiso de lectura** de esa carpeta (`s/n`): solo s, S, n y N cuentan; Enter solo no decide nada; lo demás se vuelve a preguntar y tras 3 intentos (o con la entrada cerrada) se sale sin leer. La carpeta personal y la raíz de un disco llevan una advertencia en la misma pregunta.
5. Con «s»: **resumen corto** por nivel y por agente, **lo más urgente (3)** y una nota de alcance («solo lo que pudo revisar; no significa que lo demás sea seguro»); sin hallazgos dice «no se encontró nada en lo que se pudo revisar». **`--detalle`** muestra el listado completo con códigos; `--salida` escribe el listado completo en el archivo.
6. Reporte HTML en `AgentReach-reportes` (como en la 21), con dónde quedó y qué se verá, y la pregunta de abrirlo en el navegador con la misma regla (sin Enter por defecto, 3 intentos; sin respuesta válida no se abre ni se recuerda nada). `--abrir` y `--no-abrir` saltan la pregunta.

## Pruebas
`tests/test_historia_22.py` (104, absorbe las de la 21): sin terminal no lee con ninguna opción, no existen opciones ni variables que respondan, banner y presentación, cada respuesta válida e inválida, tres intentos, entrada cerrada, resumen corto y `--detalle`, HTML, abrir. Las pruebas comunes (`tests/conftest.py`, fixture `persona_delante`) responden por la persona con ayudas que solo existen como atributos del módulo `cli` (`_interactivo`, `_preguntar_por_defecto`, `_resumen_corto_por_defecto`, `_crear_reporte_por_defecto`): ninguna es alcanzable desde la línea de comandos. Las pruebas del comando real por subproceso comprueban que sin terminal no se lee nada.

## Decisiones / para Alex
- «Sin terminal no lee nada» es global: también `--salida` y los scripts. `doctor` no pide permiso (mira la terminal y la carpeta actual, no audita).
- La pregunta de abrir el navegador solo aparece si no hay respuesta recordada.
- Sigue abierta la mejora M1 (que un agente no pueda simular una terminal y escribir la s).

## No verificado
Una corrida en una terminal real de Windows con la instalación global (las pruebas simulan la terminal).
