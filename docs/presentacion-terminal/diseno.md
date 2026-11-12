# Cómo se presenta AgentReach en la terminal

Fecha: 2026-11-09. Propuesta de diseño: no cambia código, pruebas, historias ni PRD. Complementa `docs/reporte-terminal/diseno.md` (color, `NO_COLOR`, ancho, codificación, respaldo ASCII), cuyas reglas se aplican aquí sin repetirlas. Las muestras están en `docs/presentacion-terminal/muestras/` (cada una en `.txt` sin color y `.ansi.txt` con color de 24 bits; los símbolos son Unicode salvo `banner-ascii-respaldo`). Rutas de las muestras: ejemplos inventados (`C:\Users\ejemplo\...`); ningún valor con forma de secreto.

## 1. Qué hacen otros proyectos (solo el patrón, sin copiar su arte ni sus textos)

Todo se leyó el 2026-11-09 con la API pública y `raw.githubusercontent.com`; nada se ejecutó.

### gentle-ai (repositorio `Gentleman-Programming/gentle-ai`, rama `main`)

- Estructura: `cmd/gentle-ai/main.go`, `internal/tui/` (pantallas en `screens/`, estilos en `styles/`), `internal/doctor/doctor.go`. Imagen de marca en `docs/assets/brand/` (png y gif, para el README, no para la terminal).
- Biblioteca de estilos: `lipgloss` (de Charm; verificado en `internal/tui/styles/styles.go`: https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/internal/tui/styles/styles.go). La paleta es "Rose Pine" (violeta para títulos y marco, verde azulado para éxito, durazno para porcentaje, amarillo para avisos, rojo suave para errores). El cursor es `▸ `. Marco de doble línea alrededor de la pantalla.
- Pantalla de bienvenida (https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/internal/tui/screens/welcome.go). Orden de arriba abajo: logo (opcional) -> línea de lema con la versión -> aviso de actualización (opcional) -> panel de avisos con desplazamiento (opcional) -> título "Menu" -> lista de opciones con cursor -> línea de ayuda con las teclas `j/k` navegar, `enter` elegir, `q` salir. Al estar dentro de un marco, salvo en modo compacto.
- Patrón que más vale copiar: **degradación por tamaño**. Si no cabe, quita primero el logo, luego el marco, y al final deja solo la acción principal y una ayuda corta. Nuestro banner de 3 niveles (grande, mediano, mínimo) sigue esa idea.
- Si el logo es ASCII o imagen y cómo se dibuja (`RenderLogo`): **no verificado**, no leí el archivo que lo define.
- `doctor` (https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/internal/doctor/doctor.go): el paquete solo calcula; no imprime. Cinco comprobaciones fijas (archivo de estado válido, versión de recursos instalados, servicio local alcanzable, espacio en disco, perfil gestionado) más una por cada herramienta. Cada resultado es "correcto / aviso / fallo" con un detalle y, opcional, un **remedio que se describe pero no se ejecuta** (la mayoría solo manual). Se ejecutan en orden fijo y, si una comprobación se rompe, se registra como fallo sin detener las demás. Cómo se pinta en pantalla (símbolos, colores, código de salida): **no verificado**.
- No leí `main.go` ni `shell_install_hero.go`: lo que diga la ejecución real de `gentle-ai doctor` o del "hero" del instalador es **no verificado**.

### BMAD-METHOD (repositorio `bmad-code-org/BMAD-METHOD`, rama `V6.12`)

- En `main` ya no existe `tools/cli`; el instalador está en `tools/installer/` de la rama `V6.12` (archivos `bmad-cli.js`, `cli-utils.js`, `ui.js`, `prompts.js`, `install-messages.yaml`). Fuentes: https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/V6.12/tools/installer/cli-utils.js y `.../ui.js`.
- Banner (`displayLogo`): un bloque de texto fijo con **dos variantes según el ancho de la terminal** (la ancha desde 95 columnas, la estrecha debajo; 80 si no puede medir). Colores: logo azul, lema en blanco, lema secundario y créditos atenuados, caja redondeada azul. **Sin emojis** y, en lo que leí, sin versión dentro de ese bloque. Esto **no coincide** con lo que Alex recuerda (banner cian, subtítulos con emojis, versión, "Ok to proceed? (y)"): puede ser otra versión del instalador; **no verificado**, y la frase "Ok to proceed" no la encontré en estos archivos.
- Orden del flujo (`ui.js`): banner -> mensaje de inicio de la versión -> comprobación suave de `uv` (avisa, no bloquea) -> carpeta de instalación (con confirmación "instalar aquí / crear") -> si ya hay instalación, menú de actualizar o modificar -> módulos -> herramientas/entornos -> ajustes por módulo -> indicadores de progreso (spinners) y registros -> resumen final con los avisos repetidos. Casi todo se salta con `--yes` o con indicadores en la línea de comandos.
- Patrón que vale copiar: **una pregunta solo si hay algo que decidir o algo que se va a cambiar**, y modo sin preguntas para automatizar. Lo que no se copia: instalar y configurar es justo lo que AgentReach no hace.

## 2. Principios para AgentReach

1. **Dice lo que no hace.** Toda pantalla propia termina o abre con "no modifica nada ni ejecuta ningún programa".
2. **No miente.** Sin porcentajes inventados, sin "todo bien" si no se miró; el color nunca va solo (símbolo y palabra, como en `reporte-terminal`).
3. **Poco ruido.** El banner es identidad, no contenido: nunca estorba a quien automatiza.
4. **Sin memoria.** AgentReach no escribe archivos de estado, así que no puede "mostrar el banner solo la primera vez". Por eso el banner lo decide la pantalla, no la historia del usuario.
5. **Funciona en la consola más pobre** (Windows antiguo, redirección, lectores de pantalla): hay respaldo ASCII sin tildes.

## 3. Banner: tres tamaños

Dibujo propio: letras de 5 filas por 5 columnas hechas con bloques. "AGENT" en blanco hueso `#EAF4F2` y "REACH" en menta `#3DF5D0`; el lema en gris `#A9BDB9`, la versión en `#7C928E`. Se generaron con un pequeño script de maqueta (no es código del producto). Todos miden 61 columnas o menos (máximo permitido: 72).

Grande, 6 líneas (5 de letras + lema), `muestras/banner-grande.txt`:

```text
 ███   ████ █████ █   █ █████   ████  █████  ███   ████ █   █
█   █ █     █     ██  █   █     █   █ █     █   █ █     █   █
█████ █  ██ ████  █ █ █   █     ████  ████  █████ █     █████
█   █ █   █ █     █  ██   █     █  █  █     █   █ █     █   █
█   █  ███  █████ █   █   █     █   █ █████ █   █  ████ █   █
              Know what your agents can reach.
```

Mediano, 3 líneas (medios bloques `▀ ▄ █`, dos filas de punto por línea), `muestras/banner-mediano.txt`:

```text
▄▀▀▀▄ ▄▀▀▀▀ █▀▀▀▀ █▄  █ ▀▀█▀▀   █▀▀▀▄ █▀▀▀▀ ▄▀▀▀▄ ▄▀▀▀▀ █   █
█▀▀▀█ █  ▀█ █▀▀▀  █ ▀▄█   █     █▀▀█  █▀▀▀  █▀▀▀█ █     █▀▀▀█
▀   ▀  ▀▀▀  ▀▀▀▀▀ ▀   ▀   ▀     ▀   ▀ ▀▀▀▀▀ ▀   ▀  ▀▀▀▀ ▀   ▀  v0.1.0
```

Mínimo, 1 línea, `muestras/banner-minimo.txt`:

```text
AGENT REACH  v0.1.0  ·  Know what your agents can reach.
```

Respaldo ASCII (sin ningún carácter fuera de ASCII; en `muestras/banner-ascii-respaldo.txt` están los tres niveles): el grande con `#`, el mediano como un cuadro de texto de 4 líneas con `+`, `-` y `|`, y el mínimo `AGENT REACH v0.1.0 - Know what your agents can reach.` (el "·" pasa a "-"). Aviso honesto: **no miré cómo se ven en una consola real**; los medios bloques `▀ ▄` y `█` existen en Consolas y Cascadia, pero conviene que Alex los vea.

Elección del nivel (por ancho `W` de la terminal, medido con las reglas de `reporte-terminal`):

| Ancho | Banner |
|---|---|
| `W >= 64` y alto >= 24 | el que pide la pantalla (ver sección 4) |
| `W` entre 40 y 63 | mediano no cabe (61): se baja a mínimo |
| `W < 40` o Unicode no disponible | mínimo en ASCII |

## 4. Cuándo se muestra

Regla de oro: **el banner solo aparece si la salida estándar es una terminal interactiva**.

Nunca se muestra, ninguno de los tres tamaños, cuando:
- la salida va a un archivo o a una tubería (`>`, `|`, `--salida ARCHIVO`);
- `NO_COLOR` está definida y no vacía (por coherencia con `reporte-terminal`; el banner sin color sería solo ruido; si falta algo de contexto, queda la línea mínima de texto del reporte);
- se pasó `--no-banner` (opción nueva, [SUPUESTO]) o la variable `AGENTREACH_NO_BANNER=1`;
- se pasó `--json` (la salida es solo JSON, sin una línea extra);
- `TERM=dumb`, o la terminal es más angosta que 40 columnas.

Dónde sale cada tamaño:

| Pantalla | Banner |
|---|---|
| `agentreach` sin argumentos o `--help` | grande |
| `agentreach doctor` | mediano |
| `agentreach <carpeta>` (reporte) | mínimo, como primera línea del encabezado |
| `agentreach --version` | mínimo reducido: solo "AGENT REACH 0.1.0" |
| errores (a `stderr`) | ninguno |

`--version` y los errores no llevan banner grande porque los usan otros programas para leer la versión o el motivo del fallo.

## 5. Pantallas

### 5.1 `agentreach --version` (`muestras/version.txt`)

```text
AGENT REACH 0.1.0
Python 3.12.4 en win32 (ejemplo)
Solo lectura: no modifica nada ni ejecuta ningún programa.
```

La primera línea es estable y fácil de leer por otro programa: nombre, un espacio y la versión, sin color si no hay terminal. Las otras dos son opcionales con `--version --verbose` en un futuro; para el MVP basta con la primera. Código de salida 0.

### 5.2 `agentreach doctor` (`doctor-es.txt`, `doctor-en.txt`, con `.ansi.txt`)

Comprobación **de solo lectura de este equipo**; no recibe carpeta y no analiza ningún proyecto. Comprueba, en este orden fijo:

1. Versión de Python (la mínima del proyecto es 3.12).
2. Permisos de lectura (puede listar y leer en la carpeta actual; solo mira, no escribe nada).
3. Codificación de la consola (por ejemplo `utf-8` o `cp437`).
4. Color admitido: ninguno, 16 colores o 24 bits, y por qué (según `NO_COLOR`, `COLORTERM`, `WT_SESSION`, como en `reporte-terminal`).
5. Unicode: si la consola puede escribir los símbolos del reporte (se prueba con `encode`, sin imprimir nada raro).
6. Idioma detectado y de dónde salió (configuración regional, `AGENTREACH_IDIOMA` o `--idioma`).
7. Ancho de la terminal.

Cada línea tiene símbolo y palabra: `√` correcto (menta), `▲` aviso (ámbar), y fallo `■` solo si algo impide funcionar (aquí sin rojo: el rojo queda reservado para "comprobado", así que el fallo usa ámbar con la palabra "FALLO"). Cierre fijo: **"AgentReach no modifica nada ni ejecuta ningún programa."** y el código de salida en palabras (0 sin fallos, 1 con fallos; los avisos no cuentan).

No hace ningún remedio automático (a diferencia de herramientas que ofrecen arreglar): solo da un consejo escrito. Si la consola no tiene Unicode, el propio `doctor` cambia a ASCII y lo avisa (ver `doctor-en.txt`).

### 5.3 Primera ejecución `agentreach <carpeta>` (`primera-ejecucion-es.txt`)

Lo que ve la persona, de arriba abajo:

1. Su comando.
2. Línea mínima de marca con la versión y la frase de solo lectura.
3. La carpeta que se va a revisar (ruta absoluta, única vez) y el idioma y color elegidos.
4. **Una línea de progreso** que se reescribe con retorno de carro (`\r`) y solo existe si es terminal. Muestra lo que **sí se sabe**: archivos revisados y hallazgos hasta ahora. **No hay porcentaje ni barra**, porque el total no se conoce hasta recorrer la carpeta (y recorrerla dos veces para contarla sería trabajo extra sin valor). Si la salida no es una terminal, no se imprime ninguna línea de progreso, solo el reporte.
5. Al terminar, esa misma línea queda fija con "√ listo en 1,8 s".
6. El resumen y el reporte completo definidos en `docs/reporte-terminal/diseno.md` (aquí solo se muestra la parte inicial).
7. Pista de `--detalle` y código de salida en palabras.

Si la revisión se interrumpe con Ctrl+C: una línea "Interrumpido. No se muestra un reporte parcial." y código de salida 130 (convención habitual; **no verificado** en Windows).

## 6. Instalación

Hoy (README): se ejecuta desde el código con `uv run agentreach <carpeta>`; `uv tool install agentreach` es **planeado** y el paquete no está publicado.

Propuesta cuando se publique:

```text
uv tool install agentreach==0.1.0
agentreach doctor
```

- **Versión fija** (`==0.1.0`): quien instala sabe exactamente qué recibe; no "la última".
- **Suma de verificación** (SHA-256: una huella de 64 letras y números del archivo; si el archivo cambia un solo byte, la huella cambia): se publica en la página de la versión (GitHub y PyPI). Para comprobarla antes de instalar, descargar el archivo, calcular la huella (`Get-FileHash` en PowerShell) y compararla. **No verificado** que `uv tool install` pueda exigir la huella directamente (`uv pip install --require-hashes -r requisitos.txt` sí existe para `pip` de `uv`; confirmar en la documentación de `uv` antes de prometerlo en el README).
- Se prefiere `uv tool install` porque crea un entorno aparte para la herramienta y no toca el Python del sistema.

**Por qué NO se ofrece `curl | bash`** (descargar un script y ejecutarlo de inmediato): (1) AgentReach existe para decirle a la gente qué puede alcanzar un programa; pedirle que ejecute sin leer un script de internet va contra su propia idea; (2) el script puede cambiar entre dos descargas o servirse distinto a cada persona, y no queda nada que verificar; (3) en Windows ni siquiera existe `bash` en PowerShell, y la alternativa `irm | iex` tiene el mismo problema; (4) con `uv` y una versión fija no hace falta. Es una decisión de marca, no solo técnica.

**Qué pregunta el instalador: nada.** No hay instalador propio: la instalación es el comando de `uv`, que no hace preguntas. Casi no necesita preguntas porque AgentReach no instala nada en los agentes, no modifica configuración y no necesita permisos especiales; "¿Ok to proceed?" (como en BMAD) solo tiene sentido cuando se va a cambiar algo. Dos únicas preguntas posibles, ambas solo con terminal y con respuesta por defecto segura:
- `--salida ARCHIVO` cuando el archivo ya existe: "El archivo existe. ¿Reemplazarlo? (s/N)". Sin terminal: se niega, salvo `--forzar` [SUPUESTO].
- Nada más. Si hay una duda de idioma, se usa español y se dice cuál se usó.

Después de instalar, el primer paso recomendado es `agentreach doctor`, que no lee ninguna carpeta.

## 7. Boceto de la pantalla interactiva (fase 2, solo idea)

Para navegar hallazgos cuando son muchos. Solo se abre con terminal y con `--interactivo` (o `agentreach ver`), nunca por defecto; si no hay terminal, se imprime el reporte normal. Sigue el patrón de gentle-ai (teclas `j/k`, `enter`, ayuda en la última línea, degradación por tamaño). **No verificado** qué biblioteca conviene en Windows (se podrían evaluar Textual o Rich; no las probé).

```text
AGENT REACH  mi-app          2 comprobados · 3 potenciales · 2 hipótesis
-------------------------------------------------------------------------
 ■ .env.local            línea 2   Credencial en un archivo
 ▲ .env.staging          línea 4   Credencial en un archivo
 ▲ AGENTS.md             línea 9   Archivo de instrucciones sospechoso
 ◊ enlace-externo        -         Enlace que sale de la carpeta
-------------------------------------------------------------------------
 Nivel: COMPROBADO. Existe, se puede leer y ninguna regla lo impide.
 → Qué hacer: saque la credencial del proyecto y rote la clave.
-------------------------------------------------------------------------
 j/k mover   Enter abrir detalle   / buscar   Esc volver   ? ayuda   q salir
```

- `j`/`k` (o flechas): subir y bajar. `Enter`: abre el detalle de ese hallazgo (los ocho campos). `/`: escribe un texto para filtrar por archivo o tipo. `Esc`: cierra el detalle o el filtro. `q`: sale. `?`: ayuda.
- Solo lectura: no hay tecla que abra, edite, borre ni ejecute nada. Ninguna acción cambia el disco.
- Si la terminal es angosta (<60) o de pocas líneas, se degrada: primero se quita el panel de detalle, luego queda solo la lista, y al final se imprime el reporte normal.

## 8. Decisiones pendientes de Alex

| # | Decisión | Recomendación |
|---|---|---|
| D1 | Tono: "usted" o "tú" (también en `doctor` y las preguntas) | "Usted", como el reporte (P3 de `reporte-terminal`). |
| D2 | Emojis en los títulos (estilo BMAD) | **No.** En consolas de Windows antiguas salen como cuadros o signos de interrogación y rompen el ancho; los símbolos propuestos (`■ ▲ ◊ ○ √ →`) ya dan el mismo apoyo visual y tienen respaldo ASCII. |
| D3 | Tamaño del banner | Grande solo en `agentreach` y `--help`; mediano en `doctor`; mínimo en el reporte. Si prefiere uno solo, el mediano (3 líneas). |
| D4 | ¿`doctor` entra al MVP? | **Sí, versión mínima** (las 7 comprobaciones de arriba): es la forma más barata de explicar un reporte raro (sin color, texto roto, idioma equivocado) sin pedirle datos a la persona. Si el tiempo aprieta, lo primero que se recorta es la pantalla interactiva, no `doctor`. |
| D5 | Banner en cada ejecución con carpeta o solo línea mínima | Línea mínima: no hay memoria de "primera vez" y 6 líneas en cada ejecución cansan. |
| D6 | Opciones nuevas: `--no-banner`, `--json`, `--interactivo`, `--forzar` | Aceptarlas como [SUPUESTO] hasta que se escriban las historias. |
| D7 | Medios bloques `▀ ▄ █` en el banner mediano | Verlos en la consola de Alex antes de cerrar. Si fallan, el mediano pasa a ser el mínimo en ASCII. |
| D8 | Suma de verificación en la instalación | Publicarla en la versión y, si `uv` no puede exigirla, documentar la comprobación manual con `Get-FileHash`. |

Qué no se verificó: el aspecto real en consola; el código de `main.go` de gentle-ai y su `RenderLogo`; la presentación de `doctor` en gentle-ai; el banner cian y la frase "Ok to proceed" de BMAD; que `uv tool install` acepte una huella; el código de salida 130 en Windows.
