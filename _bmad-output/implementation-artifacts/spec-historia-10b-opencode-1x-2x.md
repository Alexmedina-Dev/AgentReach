# Historia 10b: opencode 1.x y 2.x

**Estado: terminada (2026-11-10)** sin diferidos.

## Qué hace
El adaptador de opencode cubre el esquema 1.x (`permission`, objeto) y el 2.x (`permissions`, lista `{action, resource, effect}`); detecta el esquema por la forma de los archivos (`ResultadoAdaptador.esquema`: 1.x / 2.x / ambiguo; no prueba la versión instalada). Sinónimos bash=shell, task=subagent, write/patch=edit; gana la última regla que coincide. Lee global (XDG/OPENCODE_CONFIG), proyecto, `.opencode/opencode.json(c)` y gestionada. `external_directory` sin regla: ask (1.x) / allow (2.x o ambiguo, peor caso). TH-14 (MCP local en la configuración del proyecto).

## Revisión independiente: 9 hallazgos
Corregidos: 1 (fuera del proyecto rige también `read` y la base `*.env`; gana lo más restrictivo), 2 (`agents`/`permissions` por agente, `plugin(s)`, `experimental.policies` → FUNCION_NO_MODELADA), 3 (agentes `.md` en subcarpetas, sin seguir enlaces), 4 (encabezado con `---` dentro y claves entre comillas), 5 (`~\*`, `$HOME`, `${HOME}`), 7 (`permission:{}`/`permissions:[]` vacíos → ambiguo), 8 (`mcp.servers` solo es contenedor si sus valores son objetos; `command` en cadena), 9 (`*.env.example` permitido en la base).
Hallazgo 6, antes diferido, corregido el 2026-11-10: se lee el `opencode.json(c)` de las carpetas padre hasta la raíz del repo (la que tiene `.git`, comprobada solo con `lexists`; sin `.git` arriba no se mira fuera del proyecto) y el respaldo `%APPDATA%\opencode` en Windows. Pruebas en `tests/test_opencode_1x_2x.py`. Sin diferidos.
Pruebas: `tests/test_opencode_1x_2x.py` (31). Pendiente de Alex: corrida real con su opencode 1.19.0.
