# Colores del reporte de AgentReach: marca, semántica y contraste

> **Decisión de Alex (2026-11-09):** se elige la **Paleta A** (rojo solo para comprobado) y la Paleta B queda descartada. La plantilla `index-colores.html` ya no tiene el botón de la Paleta B.


Fecha de la investigación: 2026-11-09. Archivo de la propuesta: `docs/boceto-reporte/index-colores.html` (el boceto original `index.html` no se tocó). Abre `index-colores.html` y usa los botones EN/ES, Paleta A/B y Tema (oscuro/claro/sistema).

## 1. ¿El tema oscuro del boceto respetaba la marca?

Fuente de la marca: `docs/diagrama/Diagram.dc.html` (leído como texto) y los píxeles reales de `assets/agentreach-banner.png`, `agentreach-icon.png` y `agentreach-badge.png` (colores contados con un script).

Colores de la marca, medidos:

| Uso en la marca | Valor |
|---|---|
| Fondo | `#0B1114` |
| Superficie (tarjetas, badge) | `#121C20` |
| Menta (acento, flujo, "AGENT**REACH**") | `#3DF5D0` |
| Ámbar (nodo y línea de "hallazgo") | `#FFB224` |
| Texto principal | `#EAF4F2` |
| Texto secundario | `#A9BDB9` |
| Texto apagado | `#7C928E` |
| Arcos del ícono (menta atenuado) | `#1A554C`, `#299A85` |
| Aro del ámbar | `#85611C` |
| Bordes del diagrama | `#2F4044` (sólido), `#4A5C5F` (punteado), `#7C928E` (fuerte) |
| Fondos hundidos del diagrama | `#0F181B`, `#0D1518` |

Tu paleta (7 colores) coincide exactamente con la marca. **Esos 7 ya estaban bien en el boceto.** Diferencias exactas encontradas:

1. **Comprobado era ámbar en el boceto; en el diagrama oficial es menta** (pastilla "comprobado" con borde `#3DF5D0`, "potencial" ámbar `#FFB224`, "hipótesis" gris `#A9BDB9` punteado). Es la diferencia más importante, y tiene un efecto secundario: en el boceto "comprobado" y "potencial" eran del mismo color.
2. **"No se pudo revisar" y la nota "no se muestran valores" usaban menta**, que en la marca es el flujo normal. Se mezclaban con "correcto".
3. **Bordes y superficies inventados**: `#243439` (línea) y `#182529` (superficie 2) no existen en la marca. Corregido: línea `#2F4044`, fondo hundido `#0F181B`, borde punteado `#4A5C5F`.
4. **Logo inventado**: el boceto dibujaba un cuadrado con una "A". El oficial es el radar de arcos con nodos. Corregido: se copió el SVG exacto del diagrama (inline, sin cargar nada).
5. **Wordmark**: faltaba "AGENT" blanco + "REACH" menta, en mayúsculas con espaciado. Corregido.
6. **Tipografía**: el diagrama usa Space Grotesk (títulos) y JetBrains Mono (texto). El boceto usaba la fuente del sistema. Ahora las pide primero y cae a la fuente del sistema si no están instaladas; no se carga nada externo (por eso en una máquina sin esas fuentes se verá la del sistema).
7. Dos detalles de la marca que no se copiaron: la cuadrícula de puntos del banner y el aro del ámbar `#85611C` (solo decorativos).

Texto: `#EAF4F2`, `#A9BDB9` y `#7C928E` ya eran los de la marca.

## 2. Tema claro más llamativo

El claro dejó de ser blanco apagado. Decisiones:

- La barra superior sigue siendo **oscura de marca** (`#0B1114`, filo menta de 3 px) en ambos temas, así el logo y "REACH" menta se ven como en la marca.
- Fondo de página menta pálido `#DFF5EF`; tarjetas blancas `#FFFFFF`; bordes verdosos `#9CC8BE`.
- Menta oscuro `#00806B` (relleno/botones) y `#005F4D` (texto); ámbar profundo `#7A4300` (texto) con borde `#B86E00`.
- Las tarjetas de nivel y las cifras del resumen llevan fondo tintado (rojo claro, ámbar claro, violeta claro) con borde grueso, para que se lean de lejos.

## 3. Semántica de color: investigación

### Lo que dicen las fuentes (consultadas el 2026-11-09)

| Fuente | Qué dice | Estado |
|---|---|---|
| WCAG 2.2, criterio 1.4.1 Uso del color (Nivel A). https://w3c.github.io/wcag/understanding/use-of-color.html | El color no puede ser el único medio para transmitir información; hay que añadir texto, forma, patrón o icono. | Confirmado por resumen de búsqueda de las páginas W3C (WCAG 2.0/2.1/2.2; el texto del criterio no cambió). No abrí la página 2.2 directamente. |
| WCAG 1.4.3 y 1.4.11. https://www.w3.org/WAI/WCAG22/understanding/ | Texto normal 4.5:1; texto grande 3:1; iconos y bordes de controles 3:1. | Confirmado vía búsqueda (varias guías secundarias coinciden). |
| IBM Carbon, patrón de indicadores de estado. https://www.carbondesignsystem.com/patterns/status-indicator-pattern | Rojo = peligro/error, naranja = advertencia seria, amarillo = advertencia normal, verde = normal/éxito, azul = informativo/progreso, gris = pendiente, morado = atípico/indefinido. "Depender solo del color es insuficiente"; un indicador completo = icono + forma + color + etiqueta. | Leído con WebFetch. Ojo: la página dice a la vez "al menos tres elementos" y "al menos dos"; es inconsistente en la propia fuente. |
| PatternFly (Red Hat), estado frente a severidad. https://www.patternfly.org/patterns/status-and-severity/ | Separa estado (¿cómo está algo?) de severidad (¿qué tan grave?). Severidad: crítica, importante, moderada, menor, ninguna, indefinida; el icono pesa más cuanto más grave. "Texto, color e icono combinados". No se debe pintar un icono informativo con el color de peligro. | Leído con WebFetch. No da valores hex. |
| GitHub Primer. https://primer.style/foundations/color (vía borradores y unpkg `@primer/primitives` DESIGN_TOKENS_SPEC.md) | Roles: danger (rojo, errores y bloqueos que exigen acción), severe (naranja, entre atención y peligro), attention (amarillo), success (verde), accent (azul). Icono x con danger, check con success. | Solo por búsqueda y páginas borrador. No verificado en primer.style oficial. El principio "no solo color" no apareció. |
| Atlassian Design. https://atlassian.design/foundations/color y https://developer.atlassian.com/platform/forge/ui-kit/components/lozenge/ | Roles: danger ("Blocked/Failed"), warning ("At risk"), success, information ("In progress"), neutral. "No usar un acento donde el color ya tiene significado semántico." | Por búsqueda; no abrí las páginas. |
| Microsoft Fluent 2. https://fluent2.microsoft.design/color | Tokens de estado: success, warning, danger (también hay "severe warning" en versiones previas). Hex difieren según el sitio secundario consultado. | NO verificado en la fuente oficial. Solo la existencia de los roles. |
| Material Design 3 (m3.material.io, roles de color) | Roles de error: error, on-error, error-container, on-error-container; success/warning se añaden como colores personalizados fuera del esquema base. | NO verificado en m3.material.io; solo fuentes secundarias (Compose, material-components-android). |
| CVSS v4.0, FIRST. https://www.first.org/cvss/v4.0/specification-document | Escala cualitativa: None 0.0, Low 0.1-3.9, Medium 4.0-6.9, High 7.0-8.9, Critical 9.0-10.0. Define gravedad técnica, no el riesgo para tu organización. CVSS **no define colores**. | Tabla leída directamente. |
| SARIF 2.1.0, OASIS. https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | `level`: none, note, warning, error (por defecto warning). No define colores. | Solo por fuentes secundarias que lo citan; no abrí el texto normativo. |
| ISO 3864 / ANSI Z535 (colores de seguridad). Resumen: https://digital.incompliancemag.com/issue/july-2023/ansi-z535-1-safety-colors-in-focus/ | Rojo = PELIGRO (riesgo alto), naranja = ADVERTENCIA, amarillo = PRECAUCIÓN; azul = aviso no relacionado con seguridad; verde = seguridad/primeros auxilios/salidas. ANSI divide el amarillo en amarillo y naranja. Las normas definen los colores, no cómo usarlos en pantallas. | Por artículos de la industria; no tengo el texto de las normas (de pago). Los códigos Pantone/RAL varían por fuente. |
| Daltonismo. Birch 2012 (meta-análisis) citado en https://dev.to/alphashark/8-of-your-male-users-cant-see-your-red-error-states-design-for-color-blindness-2ofa | Cerca del 8% de hombres y 0.5% de mujeres tienen deficiencia rojo-verde (valores varían por fuente: 6% de hombres si solo cuentas deuteranomalía/deuteranopia). Consejo: no usar rojo y verde como única señal, variar la luminosidad, añadir icono/texto. | Cifras de blogs que citan a Birch; no abrí el artículo original. |

### Conclusiones de la investigación

1. Todas las guías serias asignan **rojo a lo más grave** (peligro, error crítico, ISO/ANSI "PELIGRO"). Ámbar/amarillo es el nivel intermedio ("advertencia/precaución"). Azul = información. Verde = correcto.
2. Ninguna fuente deja el color solo: pide **icono + forma + etiqueta** además (WCAG 1.4.1, Carbon, PatternFly).
3. Carbon y Atlassian piden que la paleta de estado **se reserve para estado** y no se use como decoración. Por eso el rojo no aparece en ningún otro lugar de la propuesta.
4. PatternFly insiste en no confundir **estado** con **severidad**. En AgentReach, Comprobado/Potencial/Hipótesis son una escala de **certeza**; la gravedad del daño depende además de la credencial. Para el reporte, donde "comprobado" = exposición confirmada, es razonable que el nivel más cierto sea el más grave visualmente. Esto es una decisión de producto mía, no una regla de las fuentes.
5. Hay un hueco de las fuentes: ninguna cubre "no se pudo revisar". Carbon usa morado/gris para "indefinido/no iniciado" y PatternFly tiene "undefined". Elegí **violeta**.

### El conflicto con la marca

En la marca el ámbar significa "hallazgo" (leyenda del diagrama: línea ámbar = hallazgo). Si todo hallazgo es ámbar, "comprobado" (lo más grave) y "potencial" no se diferencian por color; y rojo, el color que cualquier persona espera para "peligro", no existe en la marca.

## 4. Sistema propuesto

Cada color tiene un solo uso. Cada rol también tiene su icono y su forma de borde.

| Rol | Paleta A (recomendada) | Icono y forma | Paleta B (alternativa) |
|---|---|---|---|
| Comprobado: exposición confirmada, lo más grave | **Rojo** (`#FF6B6B` oscuro / `#B3201A` claro) | Octágono sólido con "!", borde grueso | Ámbar de marca, mismo octágono sólido |
| Potencial | **Ámbar** (`#FFB224` / `#7A4300`) | Triángulo con "!", borde normal | Ámbar, igual al de A (pierde distinción por color) |
| Hipótesis | **Gris** (`#A9BDB9` / `#3A524D`) | Rombo con "?", borde punteado | Igual |
| No se pudo revisar | **Violeta** (`#B9A2FF` / `#5A3DC0`) | Círculo tachado, borde discontinuo | Igual |
| Sin hallazgos / correcto | **Menta** (`#3DF5D0` / `#005F4D`) | Palomita en círculo | Igual |
| Información | **Azul** (`#6DB6FF` / `#0A58A8`) | Círculo con "i" | Igual |
| Acciones ("qué hacer", enlaces) | **Menta** de marca | Flecha, barra lateral | Igual |

Por qué la A: el rojo se reserva para una sola cosa y coincide con ISO/ANSI/Carbon/Primer; el ámbar de marca sigue siendo "potencial", lo más cercano a "hallazgo a revisar"; la marca (menta + ámbar) sigue siendo la identidad en logo, barra y botones. Costo: se aparta del diagrama oficial, que pone "comprobado" en menta; habría que actualizar ese diagrama (yo no lo toqué).

Por qué la B: no agrega rojo, es la más fiel a la marca. Costo: comprobado y potencial comparten tono y solo se distinguen por icono, grosor/estilo del borde y etiqueta; el rojo queda libre para errores de sistema (p. ej. "falló la revisión"). Es la que usaría si el equipo de marca no quiere ningún rojo.

Una doble función aceptada: **menta** significa marca, "correcto" y acción. Es un verde-azulado de polaridad positiva (lo que haces o lo que está bien), siempre acompañado de icono distinto (palomita o flecha). Si prefieres uso estrictamente único, la opción es añadir un verde de éxito aparte; no lo hice para no sumar un séptimo tono.

Otros usos del color en la propuesta: "ajeno a la tarea" ya no usa color (subrayado ondulado + negrita); el aviso "datos inventados" usa azul información.

## 5. Contraste medido (razón WCAG, script `contrast.py`, scratchpad)

Umbrales: 4.5:1 texto, 3:1 iconos y bordes de controles. Todos los textos de los roles pasan 4.5:1 también sobre su fondo tintado.

**Tema oscuro** (sobre superficie `#121C20` / fondo `#0B1114`):

| Texto | Superficie | Fondo |
|---|---|---|
| `#EAF4F2` principal | 15.44 | 16.95 |
| `#A9BDB9` secundario | 8.80 | 9.66 |
| `#7C928E` apagado | 5.24 | 5.76 |
| Rojo `#FF6B6B` | 6.24 | 6.85 |
| Ámbar `#FFB224` | 9.60 | 10.54 |
| Violeta `#B9A2FF` | 7.98 | 8.76 |
| Azul `#6DB6FF` | 8.07 | 8.86 |
| Menta `#3DF5D0` | 12.51 | 13.73 |
| Menta de marca sobre texto `#0B1114` (botón activo) | 13.73 | |

**Tema claro** (sobre superficie `#FFFFFF` / fondo `#DFF5EF`):

| Texto | Superficie | Fondo |
|---|---|---|
| `#0B1114` principal | 19.01 | 16.70 |
| `#2A4540` secundario | 10.38 | 9.11 |
| `#46635E` apagado | 6.55 | 5.75 |
| Rojo `#B3201A` | 6.69 | 5.88 |
| Ámbar `#7A4300` | 7.98 | 7.01 |
| Violeta `#5A3DC0` | 7.33 | 6.44 |
| Azul `#0A58A8` | 7.06 | 6.20 |
| Gris `#3A524D` | 8.42 | 7.40 |
| Menta `#005F4D` | 7.65 | 6.72 |
| Blanco sobre menta `#00806B` (botón activo/saltar) | 4.88 | |

Barra superior (siempre de marca): `#EAF4F2` 16.95, `#A9BDB9` 9.66, `#3DF5D0` 13.73, `#7C928E` 5.76.

Bordes de campos y botones (`--ctl`): oscuro `#7C928E` 5.24 sobre superficie; claro `#46635E` 6.55. Bordes de nivel (rojo, ámbar, violeta, gris, azul): ≥ 3:1 en ambos temas (el script lo verifica; ámbar claro se oscureció de `#E08A00` a `#B86E00` por fallar con 2.69).

Excepción aceptada: el gris punteado de marca `#4A5C5F` (2.46 sobre superficie) solo se usa en bordes decorativos (etiquetas, separadores, el borde del grupo de idioma) donde el contenido ya tiene texto y no lleva información.

## 6. Verificación visual

Capturas generadas en esta carpeta (Edge, Playwright; sin errores de consola ni desbordamiento horizontal):

- `colores-escritorio-oscuro-A.png`, `colores-escritorio-claro-A.png`, `colores-movil-oscuro-A.png`, `colores-movil-claro-A.png` (página completa, paleta A).
- `colores-escritorio-oscuro-B.png`, `colores-escritorio-claro-B.png` (alternativa B).
- `colores-top-*.png`: recortes de la parte superior, en español.

Defectos conocidos: el icono de "hipótesis" (rombo punteado con "?") es pequeño a 16 px y se lee mejor como etiqueta que como icono; en la paleta B comprobado y potencial son difíciles de separar de un vistazo; no se probó con un simulador de daltonismo real (solo se razonó con luminosidad y forma); las fuentes Space Grotesk/JetBrains Mono no se cargan (se usa la del sistema si no están instaladas).
