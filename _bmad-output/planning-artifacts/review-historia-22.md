# Revisión independiente de seguridad, historia 22 (permiso de lectura)

Fecha: 2026-11-10. Solo lectura sobre el código; los casos se ejecutaron con carpetas temporales propias (fuera del repositorio, con una carpeta personal falsa) y un contador de accesos (ganchos de auditoría de Python más envoltorios de `os.stat`, `os.scandir`, `os.listdir`, `open`, `os.path.isdir`, `os.path.realpath`, etc.). No se usó la carpeta personal real ni se tocó nada de `proyecto-prueba-agentreach`.

Resultado de las pruebas: `uv run pytest -q` da 1259 pasadas y 156 omitidas (ejecutado). `uv run ruff check src tests` da 3 errores, todos de orden de imports en `tests/reglas_no_negociables/test_sin_ejecutar_programas.py`, `test_sin_red.py` y `test_sin_valores_de_secretos.py` (ejecutado; se arregla con `ruff --fix`; gravedad baja, solo estilo). Nota: `uv run` usó Python 3.13, el proyecto declara 3.12.

Leyenda: E = verificado ejecutando; L = solo leyendo el código.

## Veredicto corto
La garantía «no lee el CONTENIDO de la carpeta sin que una persona diga s/S» se cumple frente a todo lo probado, salvo dos huecos reales: (A) un programa que abra un pseudoterminal puede escribir la `s` (la mejora M1, ya conocida, confirmada por ejecución); (B) el comando `doctor` lista la carpeta sin pedir permiso. Además hay accesos de solo metadatos antes del permiso y una escritura destructiva con `--salida`.

## Casos

| # | Caso (comando o prueba) | Resultado | Veredicto | Gravedad si falla | Verif. |
|---|---|---|---|---|---|
| 1a | `echo s \| agentreach RUTA` (subproceso real, entrada por tubería) | Código 2, «sin una terminal interactiva no lee nada»; 0 lecturas tras el permiso; solo `os.path.isdir` antes | Cumple | | E |
| 1b | `S\r\n`, `s` tres veces, `n`, entrada vacía (EOF), archivo redirigido, con `--salida`, `--abrir`, `CI=1`, `AGENTREACH_PERMITIR=1`, `CLAUDECODE=1`, `--idioma en` | Igual: código 2, nada leído | Cumple | | E |
| 1c | EOF con terminal simulada (en proceso) | Una pregunta, código 2, «sin respuesta válida», 0 lecturas | Cumple | | E |
| 1d | Ctrl+C simulado (`KeyboardInterrupt` desde la pregunta) | No lee nada, pero `main` solo atrapa `Exception`: la interrupción sale sin capturar y Python imprime una traza (con rutas internas) | Cumple la garantía; defecto de pulido | Baja. Arreglo: capturar `KeyboardInterrupt` en `main` y salir con 130 y «Cancelado, no se leyó nada» | E en proceso, traza real no vista (Ctrl+C por pseudoconsola no se entregó) |
| 2 | Respuestas inválidas (misma respuesta en las 3 preguntas): vacío, espacios, `sí`, `Sí`, `si`, `y`, `yes`, `Y`, `S `, ` s`, `s\n`, `s\n\n`, `s\r`, cadena de 1 millón de caracteres, `\x1b[32ms`, `\x1b[Fs`, `s\x00`, `\x03`, `\x1a`, `ｓ` (ancho completo), `ѕ` (cirílica), `s` + espacio invisible, `s` + diéresis combinada, `1`, `true`, `ok`, `N ` | Todas: 3 preguntas, código 2, 0 lecturas. Solo `s`/`S` leen; `n`/`N` salen tras 1 pregunta | Cumple | | E |
| 3a | Ruta como argumento (absoluta, MAYÚSCULAS, relativa, sin ruta, `.`, `..`) | Siempre pregunta; la ruta mostrada es `abspath` y es la misma que luego se lee (`auditar` también usa `abspath`) | Cumple | | E |
| 3b | Enlace (junction, `mklink /J`) a la carpeta; `enlace\..` | Pregunta, pero muestra la ruta DEL ENLACE sin decir que apunta a otra carpeta; se lee el destino. `enlace\..` se normaliza por texto (lee la carpeta que contiene el enlace, igual que lo mostrado) mientras `isdir` y la advertencia usan la resolución del sistema | Cumple en lo esencial; no determinado el efecto en otros sistemas | Baja. Arreglo: mostrar también la ruta real (`realpath`) cuando difiere de la escrita, y resolver una sola vez y usar esa misma ruta para avisar, preguntar y leer | E |
| 3c | 8.3 (`CARPET~1`), MAYÚSCULAS, barra final, junction a la carpeta personal, `HOME\enlace\..` | La advertencia de carpeta personal sale en todos (usa `realpath` + `normcase`); se muestra la forma escrita (8.3 o MAYÚSCULAS), no la larga | Cumple | | E |
| 3d | Nombre de carpeta con caracteres bidireccionales/invisibles | El aviso los escapa (`\u202e`, `\u200b`) | Cumple | | E |
| 4a | Raíz de disco: `C:\`, `C:/`, `C:\.`, `\\?\C:\`, `\\localhost\C$\`, `C:\Windows\..`, sin ruta con cwd en la raíz | Todos muestran la advertencia adicional («la raíz de un disco»); con `n` no se lee nada | Cumple | | E |
| 4b | Carpeta personal (indicada con `--home`) | Advertencia adicional siempre. Si se pasa `--home OTRA`, la carpeta personal real deja de marcarse (el usuario lo pidió con la bandera) | Cumple | Muy baja | E |
| 4c | `C:\Users` (padre de las carpetas personales de todos) | Pregunta sin la advertencia; el recorrido tocaría varias carpetas personales | Falla parcial (no pedido en la spec) | Baja. Arreglo: advertir también si la carpeta CONTIENE la carpeta personal | E |
| 5a | Variables `NO_COLOR`, `CI`, `TERM=dumb`, `AGENTREACH_PERMITIR/YES/AUTO/PREGUNTAR/NO_BANNER/ASCII/IDIOMA`, `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `OPENCODE` | Ninguna salta la pregunta ni lee antes (con y sin terminal) | Cumple | | E |
| 5b | Banderas `--no-banner`, `--salida`, `--formato html`, `--abrir`, `--no-abrir`, `--sin-reporte-html`, `--idioma en`, `--json`, `--tarea`, `--directorio-de-trabajo`, `--home`, `--tema`, `--color`, `--ascii`, `--ancho`, `--detalle`, `--agente`, `--estricto`, `--incluir-ubicaciones-sensibles` | Ninguna salta la pregunta. Con `--abrir`/`--no-abrir` se salta solo la de abrir el navegador | Cumple | | E |
| 5c | Accesos antes del permiso | Solo metadatos de la propia carpeta: `os.path.isdir` (incluso sin terminal), `os.path.realpath` (aviso de carpeta personal) y, con `--salida`, `realpath`/`exists` en `dentro()`. Nunca `open`, `scandir`, `listdir` ni recorrido. Esto revela si la carpeta existe, no su contenido | Cumple en contenido; toca metadatos | Muy baja. Arreglo opcional: comprobar el terminal antes de `isdir` | E |
| 6 | Pseudoterminal: programa con `ctypes` de la biblioteca estándar crea una pseudoconsola (ConPTY, `CreatePseudoConsole`), lanza `agentreach` dentro y escribe `s\r` | `isatty` da verdadero en entrada y salida; sale la pregunta; con `s` se leyó la carpeta (257 accesos tras el permiso) y se creó el reporte. Con Enter x3 no lee; con `n` «No se leyó nada» | **Falla** (M1 confirmada y trivial en Windows con solo la biblioteca estándar) | Alta para el modelo «un agente no puede autorizar»; ya aceptada como mejora posterior. Arreglo: leer la confirmación de `CONIN$` (Windows) o `/dev/tty` y no de la entrada estándar, detectar agentes por proceso padre y variables, y no prometer más de lo que se garantiza | E |
| 6b | `isatty` con dispositivo `NUL` en la entrada y la salida | Python da `True` para `NUL`: AgentReach cree que hay terminal, pregunta, lee EOF y sale sin leer | Cumple (no autoriza), pero muestra que `isatty` es una prueba débil | Baja | E |
| 7a | ¿Se escribe algo antes del permiso? Con `n`, respuesta inválida, Enter, sin terminal, con `--salida` | Nada: ni archivo de salida, ni reporte, ni preferencias; el árbol temporal completo no cambió | Cumple | | E |
| 7b | Reporte HTML y preferencias | Solo en `<home>/AgentReach-reportes` (nombre con `x`, no pisa). Con `--home` dentro de la carpeta revisada o ruta relativa: no se escribe (avisa). Nunca dentro de la carpeta analizada | Cumple | | E |
| 7c | `--salida` hacia un archivo existente fuera de la carpeta (también `~/.agentreach/config.toml`) | **Lo sobrescribe sin avisar ni pedir confirmación** (modo `w`). Dentro de la carpeta analizada (directo, por junction, con `..`, flujo alterno `:flujo`/`::$DATA`, enlace duro) se rechaza con código 2; `NUL`, `CON` y un directorio también dan 2 | Falla parcial | Media. Arreglo: negarse si el archivo ya existe (o pedir S/N), abrir con modo `x`, rechazar enlaces y destinos fuera de una carpeta de reportes salvo confirmación | E |
| 7d | `preferencias.json` plantado por otro programa (`{"abrir_en_navegador": true}`) | Salta solo la pregunta de abrir el navegador; la de leer sigue (1 pregunta, con `n` lee 0). Si es un enlace duro a otro archivo, `guardar_preferencia` lo sobrescribe con ese JSON | Cumple para la lectura; escritura a través de enlace duro | Baja (quien puede plantarlo ya puede escribir en esa carpeta). Arreglo: abrir con `x` y comprobar `st_nlink` como hace `dentro()` | E |
| 7e | `doctor RUTA`, con y sin terminal | **No pide permiso y llama a `os.scandir` + `os.access` sobre la carpeta** (lee el primer nombre del listado y lo descarta). También `doctor --salida` escribe sin terminal y pisa un archivo existente | **Falla** respecto de «no lee nada sin permiso» (la spec lo acepta explícitamente) | Media-baja: no muestra nombres, solo «puede leer / no puede leer». Arreglo: en `doctor` usar solo `os.access` sobre la carpeta, o pedir S/N si se indicó una ruta | E |
| 8 | Huella (nombre, tamaño, fecha de modificación y hash de contenido) del árbol antes y después, con `s` + abrir `s` | Idéntico; sin valores de secretos en la salida; sin procesos ni red | Cumple | | E |

## Qué no se verificó
- Linux y macOS (`/dev/tty`, `os.isatty` sobre `/dev/null`, pseudoterminales POSIX): solo se leyó el código.
- Una terminal real de Windows con la instalación global (la propia spec lo declara no verificado).
- Ctrl+C real en consola: la pseudoconsola no entregó la interrupción; solo se simuló en proceso.
- Inyección de teclas en la consola de la persona (`AttachConsole` + `WriteConsoleInput`) y `CONIN$`: no se probó; por lectura, el código usa `input()` sobre la entrada estándar, así que no lo impide.
- Contenido del HTML (escape de nombres, secretos) y el resto del reporte: fuera de alcance de esta revisión.

## Orden sugerido de arreglos
1. `doctor` sin `scandir` (o con permiso) y con la misma regla de `--salida`.
2. `--salida`: no pisar archivos existentes sin confirmar; modo `x`.
3. M1 (confirmación desde el dispositivo de consola real) cuando se retome.
4. Mostrar la ruta real cuando es un enlace; advertir si la carpeta contiene la carpeta personal.
5. Capturar `KeyboardInterrupt`; arreglar los 3 errores de `ruff`.
