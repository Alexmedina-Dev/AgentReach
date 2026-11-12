---
name: AgentReach
status: final
version: "0.1"
created: 2026-11-11
updated: 2026-11-11
sources:
  - _bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md
  - _bmad-output/planning-artifacts/epics.md
  - docs/reporte-terminal/diseno.md
  - docs/presentacion-terminal/diseno.md
  - docs/boceto-reporte/colores.md
description: Herramienta de terminal que audita, en solo lectura, a qué puede acceder un agente de IA. Identidad sobria, técnica y honesta; el color nunca va solo.
colors:
  brand-bg: '#0B1114'
  brand-surface: '#121C20'
  brand-ink: '#EAF4F2'
  brand-mint: '#3DF5D0'
  brand-mint-neutral: '#07856C'
  brand-muted: '#767676'
  text-secondary: '#A9BDB9'
  text-quiet: '#7C928E'
  verified: '#FF6B6B'
  potential: '#FFB224'
  hypothesis: '#A9BDB9'
  unchecked: '#B9A2FF'
  ok: '#3DF5D0'
  info: '#6DB6FF'
  text-secondary-light: '#2A4540'
  text-quiet-light: '#46635E'
  page-light: '#DFF5EF'
  surface-light: '#FFFFFF'
  verified-light: '#B3201A'
  potential-light: '#7A4300'
  hypothesis-light: '#3A524D'
  unchecked-light: '#5A3DC0'
  ok-light: '#005F4D'
  info-light: '#0A58A8'
  action-fill-light: '#00806B'
typography:
  terminal:
    fontFamily: 'Monoespaciada de la terminal de la persona (no se elige)'
  html-title:
    fontFamily: 'Space Grotesk, fuente del sistema como respaldo'
  html-body:
    fontFamily: 'JetBrains Mono, fuente del sistema como respaldo'
rounded:
  sm: 4px
  md: 8px
spacing:
  indent: 2 columnas
  banner-air: 3 líneas
  work-width-min: 60 columnas
  work-width-max: 100 columnas
components:
  banner-large: { height: 6 líneas, minWidth: 64 columnas, minHeight: 24 líneas }
  banner-medium: { height: 3 líneas, width: 61 columnas }
  banner-minimal: { height: 1 línea }
  level-chip-verified: { symbol: '■', fallback: '[!!]', color: '{colors.verified}', colorLight: '{colors.verified-light}', ansi16: 91 }
  level-chip-potential: { symbol: '▲', fallback: '[!]', color: '{colors.potential}', colorLight: '{colors.potential-light}', ansi16: 33 }
  level-chip-hypothesis: { symbol: '◊', fallback: '[?]', color: '{colors.hypothesis}', colorLight: '{colors.hypothesis-light}', ansi16: 37 }
  level-chip-unchecked: { symbol: '○', fallback: '[-]', color: '{colors.unchecked}', colorLight: '{colors.unchecked-light}', ansi16: 95 }
  level-chip-ok: { symbol: '√', fallback: '[ok]', color: '{colors.ok}', colorLight: '{colors.ok-light}', ansi16: 96 }
  info-mark: { symbol: '(i)', color: '{colors.info}', colorLight: '{colors.info-light}', ansi16: 94 }
  explanation-block: { labelColor: '{colors.text-secondary}', rounded: '{rounded.sm}' }
  how-to-read: { element: details, rounded: '{rounded.md}', surface: '{colors.brand-surface}', surfaceLight: '{colors.surface-light}' }
---

## Brand & Style

AgentReach se escribe AGENT/REACH y su lema, siempre en inglés, es «Know what your agents can reach.». Es una herramienta de auditoría en solo lectura: su identidad es la de un instrumento de medición, no la de un antivirus. Sobria, precisa, sin dramatismo y sin promesas: nunca decora con «seguro», escudos ni candados. Cuando algo no se pudo comprobar, el diseño lo dice con la misma claridad con que dice lo que sí se comprobó.

La terminal es la superficie principal y manda: lo que no funcione en la consola más pobre (Windows antiguo, redirección, lector de pantalla) no es parte del diseño. El reporte HTML es la versión extendida, con la misma paleta y los mismos símbolos. Sin emojis en ninguna parte (en consolas antiguas salen como cuadros y rompen el ancho).

## Colors

Fuente de verdad de los valores: `docs/boceto-reporte/colores.md` (Paleta A, elegida por Alex el 2026-11-09). Cada color tiene un único uso.

**Marca.** `{colors.brand-bg}` es el fondo de marca, `{colors.brand-ink}` el blanco hueso de «AGENT», `{colors.brand-mint}` el menta de «REACH» sobre fondo oscuro. Menta también significa «correcto» y «acción», siempre con un símbolo distinto (√ o →).

**Niveles (Paleta A).** Rojo solo para comprobado; no se usa en ningún otro lugar.

| Nivel | Palabra | Oscuro | Claro | ANSI 16 |
|---|---|---|---|---|
| Comprobado | COMPROBADO / VERIFIED | `{colors.verified}` | `{colors.verified-light}` | 91 rojo brillante |
| Potencial | POTENCIAL / POTENTIAL | `{colors.potential}` | `{colors.potential-light}` | 33 amarillo |
| Hipótesis | HIPÓTESIS / HYPOTHESIS | `{colors.hypothesis}` | `{colors.hypothesis-light}` | 37 blanco |
| No se pudo revisar | NO SE PUDO REVISAR / COULD NOT CHECK | `{colors.unchecked}` | `{colors.unchecked-light}` | 95 magenta brillante |
| Sin hallazgos / acción | SIN HALLAZGOS / NO FINDINGS | `{colors.ok}` | `{colors.ok-light}` | 96 cian brillante |
| Información | (i) | `{colors.info}` | `{colors.info-light}` | 94 azul brillante |
| Texto secundario | | `{colors.text-quiet}` | `{colors.text-quiet-light}` | 90 gris oscuro |

**El color nunca es la única señal.** Cada nivel siempre lleva símbolo y palabra, y además forma de borde en el HTML (grueso, normal, punteado, discontinuo). Ver Components.

**Logo adaptativo (decisión de la Historia 29; AGENT y REACH deben combinar sobre cualquier fondo).**
- Con fondo conocido: REACH conserva el matiz menta y mueve solo la luminosidad hasta lograr ≥3:1 contra ese fondo; AGENT usa `{colors.brand-ink}` o `{colors.brand-bg}`, el de más contraste.
- Sin saber el fondo (hoy el caso normal; la detección del fondo real, OSC 11, es la Historia 31): AGENT usa el texto normal de la terminal y REACH usa `{colors.brand-mint-neutral}`, que da ≥4,5:1 sobre blanco y sobre negro. En 16 colores, REACH usa el cian normal (36).
- Versión y lema: gris `{colors.brand-muted}` sin tema, legible sobre blanco y negro.
- Nunca se pinta el fondo de la terminal: se respeta la de la persona.

## Typography

Terminal: la fuente monoespaciada de la persona; AgentReach no la elige ni la cambia. La jerarquía se logra con mayúsculas en los títulos de sección, sangría y el color de los niveles, no con tamaños. Sin cursiva ni subrayado (no existen en todas las consolas).

HTML: títulos en Space Grotesk y texto en JetBrains Mono (`{typography.html-title}`, `{typography.html-body}`), con la fuente del sistema como respaldo; no se carga nada externo, así que sin esas fuentes instaladas se ve la del sistema. Texto base mínimo 16 px, interlínea cómoda, párrafos de máximo ~70 caracteres en las explicaciones largas.

## Layout & Spacing

**Terminal.** El ancho de trabajo es el de las columnas reales de la terminal, acotado a `{spacing.work-width-min}`–`{spacing.work-width-max}` para el reporte (si la terminal tiene menos de 60, se usa 60). Sangría de `{spacing.indent}`. Alrededor del banner van `{spacing.banner-air}` líneas de aire, arriba y abajo.

**Todo texto impreso se ajusta al ancho (decisión de la Historia 30).** La bienvenida, las dos preguntas de permiso, los avisos y «reporte guardado» pasan por un solo punto de ajuste y nunca parten una palabra. Una ruta sin espacios va entera aunque exceda el ancho; «(S/N)» no se separa del resto de la pregunta. Límite conocido: una ruta con espacios muy larga puede partirse entre palabras. El ancho se mide por columnas visibles, no por caracteres (los símbolos y las secuencias de color no cuentan).

**HTML.** Una columna de lectura, con tarjetas sobre `{colors.brand-surface}` (oscuro) o `{colors.surface-light}` sobre `{colors.page-light}` (claro). Margen lateral de 16 px en móvil, sin desplazamiento horizontal de la página. Barra superior siempre oscura de marca, en ambos temas.

## Components

**Banner.** Tres tamaños, elegidos por ancho `W` (`{components.banner-large}`, `{components.banner-medium}`, `{components.banner-minimal}`): grande de 6 líneas si `W ≥ 64` y alto ≥ 24; mediano de 3 líneas (61 columnas) si cabe; mínimo de 1 línea («AGENT REACH  v0.1.0  ·  Know what your agents can reach.») si `W` está entre 40 y 63; bajo 40 columnas o sin Unicode, mínimo en ASCII. Cada tamaño tiene respaldo ASCII sin tildes (`#`, `+`, `-`, `|`; el «·» pasa a «-»). Nunca sale si la salida va a un archivo o tubería, con `--json`, `NO_COLOR` o `TERM=dumb`.

**Chip de nivel.** Símbolo, espacio, palabra, en el color del nivel: `■ COMPROBADO`, `▲ POTENCIAL`, `◊ HIPÓTESIS`, `○ NO SE PUDO REVISAR`. Con `--ascii` o `AGENTREACH_ASCII=1`: `[!!]`, `[!]`, `[?]`, `[-]`. En HTML el chip añade forma de icono (octágono, triángulo, rombo, círculo tachado) y borde (grueso, normal, punteado, discontinuo).

**Sección de terminal.** Título en MAYÚSCULAS con el conteo entre paréntesis (`LO MÁS URGENTE  (3 de 5)`), una línea en blanco antes, contenido con sangría. Se escribe de una vez; los colores se cierran con el código de «volver a normal» en cada trozo.

**Tarjeta de hallazgo.** Una línea: chip, agente, título corto, ruta. Debajo, solo en `--detalle` o en el HTML, los ocho campos y el bloque de explicación. Nunca contiene valores de secretos. Los identificadores técnicos (TH-n, `hooks.PreToolUse`) van únicamente junto a su explicación o en `--detalle`.

**Bloque de explicación «qué es / qué significa para ti».** Dos o tres rótulos fijos en `{colors.text-secondary}` («Qué es», «Qué significa para ti», «Qué puedes hacer»), seguidos de texto en el color normal. Termina con una acción marcada con `→` (respaldo `->`) en `{colors.ok}`. Es el único formato de explicación; terminal y HTML lo comparten, con una frase en la terminal y las tres partes en el HTML.

**`<details>` «Cómo leer este reporte».** Plegable, cerrado por defecto, entre el resumen y las vistas. Superficie `{components.how-to-read}`, esquinas `{rounded.md}`, marcador visible y operable con teclado, borde ≥3:1. Dentro: las fichas del glosario, un ejemplo por nivel y por agente.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Símbolo + palabra + color en cada nivel | Comunicar un nivel solo con el color |
| Rojo únicamente para «comprobado» | Usar rojo para errores del sistema o decoración |
| Ajustar todo al ancho, sin partir palabras ni rutas | Cortar una ruta o separar «(S/N)» |
| Respaldo ASCII sin tildes en cada símbolo y banner | Emojis, escudos, candados, «seguro» o «sin riesgo» |
| Logo con AGENT y REACH que combinan en claro, oscuro y fondo desconocido | Un solo color de logo fijo (`#3DF5D0` sobre fondo blanco no se lee) |
| Pintar solo texto; cerrar cada color | Pintar el fondo de la terminal |
| Mostrar la versión y el lema en gris `{colors.brand-muted}` sin tema | Versión o lema con el color del tema |
| Misma paleta y símbolos en terminal y HTML | Dos vocabularios visuales distintos |
