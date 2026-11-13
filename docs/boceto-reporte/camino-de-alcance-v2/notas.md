# Camino de alcance v2: notas (2026-11-09)

Archivo: `camino-de-alcance-v2.html` (un solo archivo, HTML/CSS/JS/SVG puros, sin red, sin guardar datos). Capturas y un PDF de impresión en `capturas/`. Los originales (`camino-de-alcance/`) no se tocaron.

## 1. Qué aprendí de la investigación (consultas del 2026-11-09)

Lo que leí directamente (WebFetch) y lo que solo vi en resúmenes de búsqueda va marcado.

| Fuente | Qué dice | Estado |
|---|---|---|
| GitHub, "About code scanning alerts" https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/about-code-scanning-alerts | Severidad Error/Warning/Note; para CodeQL, además Critical/High/Medium/Low (basada en CVSS) que tiene prioridad al mostrarse. Cada alerta muestra herramienta, línea que la dispara, cuándo se introdujo; etiquetas de categoría por ruta (Generated, Test, Library, Documentation); estado por rama ("Affected branches"); varias rutas de datos se agrupan en una sola alerta. | Leído |
| GitHub, "Assessing code scanning alerts" https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/assessing-code-scanning-alerts-for-your-repository | Lista con filtros desplegables y búsqueda de texto con sintaxis (`is:open`, `severity:high`, `branch:`, `tag:`, `-` para excluir); lista solo de la rama por defecto salvo que se filtre; "Show paths" numera la ruta de origen a destino. | Leído. La página no describe permalinks ni la ruta:línea mostrada. |
| Trivy, reporting https://trivy.dev/latest/docs/configuration/reporting/ | Formatos table (por defecto), JSON, SARIF 2.1.0, plantilla (HTML, JUnit), `trivy convert` de JSON a otros; `--severity` filtra; el informe en tabla empieza con un "Report Summary" por objetivo con conteos; `-` significa "no se escaneó" y `0` "se escaneó y no hubo nada"; resultados agrupados por objetivo con ID, severidad, estado, versión y título. | Leído. Idea adoptada: distinguir "no revisado" de "cero". |
| Semgrep AppSec Platform https://semgrep.dev/docs/semgrep-code/findings (y /semgrep-supply-chain/view-export) | Por defecto muestra los hallazgos prioritarios; filtros de estado, proyecto, etiquetas; "Group & sort"; exporta CSV (la exportación ignora los filtros de pantalla y el tope de la UI es 10 000 filas; más, por API); triage con motivo (falso positivo, riesgo aceptable, sin tiempo) y triage en bloque. | Solo resumen de búsqueda; no abrí las páginas. |
| SARIF 2.1.0 (OASIS) https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | GUID RFC 4122 como identificador estable (§3.5.3); `partialFingerprints` con versión `/v2` para identificar un resultado entre ejecuciones (§3.5.4.2). | Leí solo el primer tercio del documento. `level` (§3.27.10), `baselineState` (§3.27.24) y `region.startLine` solo los vi en el índice: NO verificados en el texto normativo. |
| Visores de SARIF: Microsoft SARIF Viewer, Trail of Bits SARIF Explorer, JetBrains https://github.com/microsoft/sarif-vscode-extension , https://blog.trailofbits.com/2024/03/20/streamline-the-static-analysis-triage-process-with-sarif-explorer/ | Agrupar por columna (incluida severidad), ordenar, filtro de texto con "match case"; el orden y el agrupado se recuerdan; JetBrains filtra por Error/Warning/Note/None; SARIF Explorer filtra por nivel y ayuda al triage. | Solo resumen de búsqueda de un espejo del README; no abrí el repositorio oficial. |
| SonarQube, "Retrieving issues" https://docs.sonarsource.com/sonarqube-server/user-guide/issues/retrieving | Filtros en barra lateral izquierda y resultados a la derecha; cada tarjeta lleva proyecto y ruta de archivo; el interruptor "Issues in new code" frente a código completo (esto es la idea de comparar con lo anterior). | Solo resumen de búsqueda (mi WebFetch dio "página no encontrada"). Un "Issue copy link" aparece citado en un pie de imagen: NO confirmado cómo funciona. |
| Snyk | No consulté la documentación de Snyk. | NO verificado |
| Informes de pruebas de intrusión (Astra, Bright Defense, BrowserStack, Redfox, SecureLayer7, Wiz; no oficiales) https://www.getastra.com/blog/security-audit/penetration-testing-report/ https://www.wiz.io/pt-br/academy/penetration-testing-report | Esqueleto común: resumen ejecutivo (alcance, fechas, riesgo global) para lectores no técnicos, metodología, hallazgos, plan de remediación y reprueba. Cada hallazgo con ID único, título, severidad y puntaje, activo afectado, ubicación exacta, descripción, acceso requerido, pasos para reproducir, evidencia; mismo orden de campos en todos. Advierten que ordenar solo por CVSS puede esconder lo que más importa. | Blogs de proveedores, solo resúmenes de búsqueda. No hallé plantillas PTES ni OWASP: NO verificado. |

Patrón que se repite (lectura rápida frente a lectura detallada): resumen arriba con conteos por severidad, luego una lista/tabla ordenable y filtrable, y el detalle solo al abrir una fila. Los auditores piden identificador estable, ubicación exacta y exportable; los programadores piden ruta:línea copiable y filtros.

### Qué adopté y por qué

- **Resumen arriba** (tarjetas por nivel con conteo, barra proporcional, archivos/carpetas/tipos/efectos y "Empiece aquí" con los 3 primeros Comprobados): es la lectura rápida. Las tarjetas son además los filtros de nivel (un solo control).
- **Tabla ordenable y filtrable** como vista principal con muchos datos: ordenar por nivel, ID, ubicación, tipo, efecto, agente (`aria-sort`); filtros por nivel, carpeta, tipo y texto (`/` enfoca la búsqueda); agrupar por carpeta/tipo/nivel con grupos plegables; "ver más" de 100 en 100.
- **ID estable**: `AR-` + hash FNV-1a de agente, tipo, ruta y línea (es mi propuesta, no el GUID de SARIF; sirve igual entre ejecuciones mientras no cambie la ruta o la línea, lo que es una debilidad conocida de las huellas por línea).
- **Ruta:línea copiable** (botón por fila) y **enlace permanente** (`#agent=A&size=60&f=AR-…`; en la demo el tamaño va en el enlace para reproducir los mismos datos).
- **Exportar** JSON y CSV del agente y los filtros activos (el CSV neutraliza celdas que empiezan con `= + - @`). Semgrep exporta sin filtros; aquí exporta lo filtrado y la pantalla lo dice en el contador.
- **Impresión/PDF**: vista Print en blanco y negro, todas las filas, encabezado de tabla repetido, filas sin cortarse entre páginas, detalles de los 8 campos, sección "Qué no pudo revisar" y aviso de secretos. Con más de 60 hallazgos imprime el detalle solo de los Comprobados y lo dice.
- **Teclado**: `/` buscar, `g` `t` `l` `p` vistas, flechas en el grafo y en las pestañas de agente, `+`/`-` para expandir o plegar, Esc.
- **Distinguir "no revisado" de "cero"** (Trivy): el efecto sigue marcándose "no comprobado" y la sección fija de límites no cambia.
- **Solo describo, fase 2, no implementado**: comparar con la ejecución anterior (SonarQube "new code", GitHub "affected branches", SARIF `baselineState`). El ID estable es el requisito previo.
- **No adopté**: triage con estados y asignados (el reporte es de solo lectura), paginación en servidor, filtros con sintaxis de consulta (`severity:high`) por ser demasiado para esta etapa.

## 2. Cómo se adapta el espacio al tamaño (Tarea B)

El reporte es **por agente**: pestañas de agente arriba; cada agente tiene sus propios niveles y significados (en la demo A tiene 3 niveles, B solo Comprobado y Potencial, C solo Potencial e Hipótesis). Los conteos, filtros, grafo, tabla y exportación son de un solo agente; nunca hay nodos mezclados.

Nada de alturas fijas por fila. El layout se calcula así:

1. **Modo**: hasta 12 caminos, "detalle completo" (una caja por lugar, como el boceto original). Con más, "agrupado": la columna Dónde se agrupa por carpeta; la profundidad de ruta baja sola (3, 2, 1 niveles) hasta que haya como máximo 14 grupos; una carpeta con un solo hallazgo muestra el archivo directamente.
2. **Densidad** por el número de cajas de la columna más larga: hasta 6 cajas, amplia (texto de 14 px, subtítulo completo); hasta 14, media; más, compacta (contador en insignia, subtítulo oculto salvo el de "no comprobado", y el de archivo dentro de carpeta expandida).
3. **Alturas medidas del DOM** (las cajas envuelven el texto, no se recorta ninguno); cada columna se reparte en vertical con separación mínima según la densidad y el alto total sale de la columna más alta. Resultado medido: H = 625 px con 5, 998 con 20, 818 con 60, 924 con 300 (agrupado), y 3595 con 300 y todas las carpetas expandidas.
4. **Anchos**: columnas de 167 px en detalle (separación mínima de 96 px para las etiquetas "no comprobado"), 182 a 190 en agrupado; se recalcula al redimensionar.
5. **Aristas agregadas** con grosor proporcional al logaritmo de caminos que comparten el tramo (el tramo discontinuo sigue siendo discontinuo). Sin animación de flujo si hay más de 40 aristas; sin desenfoque pesado si hay más de 40 cajas.
6. **Carpetas plegables**: clic selecciona, doble clic o botón la expande; muestra 8 archivos y una caja "+ N más" con "Ver 8 más". "Expandir todas / Plegar todo".
7. **Resumen lateral** (en lugar de mini-mapa): niveles del agente con su significado, carpetas con más caminos (clic filtra) y, al seleccionar una caja, la lista de caminos que pasan por ella.
8. **Vista por defecto**: con más de 60 hallazgos abre en Tabla (el grafo queda como panorama agrupado). Debajo de 760 px el grafo se sustituye por la Lista accesible (carpetas `<details>`), la tabla se vuelve tarjetas y no hay desborde horizontal de página.
9. **Tabla**: densidad por tamaño (amplia hasta 20, normal hasta 60, densa más); 100 filas y "Ver más"/"Ver todas".

Reglas de honestidad conservadas: continua = comprobado, discontinua = "no comprobado" (también en la etiqueta del tramo en detalle, el encabezado de columna y el subtítulo del efecto); iconos y formas de nivel además del color; nodos compartidos unidos; sección fija "Qué no pudo revisar" (con "N archivos más" plegado); aviso "No se muestran valores de secretos"; 8 campos en el panel; EN/ES; claro/oscuro; lista accesible; teclado.

Datos de prueba: botón "Demo size 5 / 20 / 60 / 300" (hallazgos del primer agente; B recibe el 40 % y C el 20 %). Generador con semilla fija, rutas ficticias `demo-app/...ejemplo`, sin valores con forma de secreto ni rutas de la máquina de Alex.

## 3. Cristal visible en oscuro (Tarea C)

Antes (v1): el fondo oscuro tenía degradados muy suaves y casi nada nítido detrás, así que el desenfoque no tenía qué desenfocar. Ahora hay, detrás de todo: malla de 5 degradados radiales (menta, violeta, ámbar, azul; hasta 74 % de opacidad), anillos y líneas de trazo nítido de la paleta, repetidos en mosaico de 1600x1400 px (sin costuras ni cortes), y ruido sutil. Los paneles llevan tinte translúcido de 40 a 52 %, `backdrop-filter: blur(22px) saturate(170%) brightness(.5)`, borde superior de 1 px con gradiente de brillo, sombra interior suave y ruido. Respaldo sólido con `@supports not (backdrop-filter)` y con `prefers-contrast: more`.

Lo importante que aprendí: el cristal translúcido y el contraste 4.5:1 chocan. Con la mancha de color detrás, el texto gris `#A9BDB9` o el rojo `#FF6B6B` fallaban. Pasos medidos: tinte 62 % fallaba; 76 % pasaba casi todo pero el cristal se veía MENOS que en v1; la solución fue **oscurecer lo que hay detrás con `brightness(.5)` dentro del `backdrop-filter`** y mantener el tinte bajo. Además hay "chips" opacos detrás del texto rojo de nivel y fondos hundidos en detalles y límites.

Medición del efecto (captura con y sin `backdrop-filter`, diferencia media de píxeles dentro de los paneles de cristal, escala 0 a 255):

| | v1 oscuro | v2 oscuro | v1 claro | v2 claro |
|---|---|---|---|---|
| diferencia media | 2.01 | 7.84 | 2.59 | 3.02 |
| % de píxeles con cambio notable | 4.6 | 17.0 | 5.0 | 3.1 |

Es decir, en oscuro el efecto es unas 4 veces mayor que antes. Lo comprobé también mirando las capturas (se ven los anillos y el brillo de color desenfocados dentro de los paneles). Honestamente: en las capturas el efecto es evidente en los bordes y sobre los anillos, pero el interior de los paneles con mucho texto sigue siendo oscuro a propósito (por el contraste); el cristal más "de revista" no cabe junto con 4.5:1.

Contraste sobre píxeles reales (script `contrast.py`: texto oculto, captura, muestreo del fondo tras cada fragmento de texto, percentil 1 de la razón WCAG, umbral 4.5:1 y 3:1 para texto grande; 24 configuraciones: oscuro y claro, escritorio y móvil, 5/20/60/300, grafo, tabla y lista, con y sin selección): resultado: 0 fallos en las 24 configuraciones; mínimo 4.71 en oscuro (móvil, lista) y 5.19 en oscuro de escritorio; mínimo 4.88 en claro (es el texto blanco sobre el botón menta `#00806B`). Excepciones no medidas: contenido de `<select>`, marcadores de posición y texto atenuado a propósito.

## 4. Verificación hecha (Edge instalado, Playwright)

- Capturas PNG (escritorio 1440 y móvil 390; oscuro y claro; 5, 20, 60 y 300; vistas Graph, Table y Print) en `capturas/captura-<dispositivo>-<tema>-<tamaño>-<vista>.png`. Print se captura con `emulate_media('print')`; también `capturas/impresion-60.pdf` (158 KB, generado por Edge).
- Extras: ES con selección (20), carpeta expandida (60), 300 con todas las carpetas expandidas, tabla con detalle, móvil arriba.
- 0 errores o avisos de consola y 0 peticiones de red en todos los recorridos; sin desborde horizontal de página (1440 y 390); 0 cajas solapadas y 0 cajas con texto recortado en el grafo (también con 300 y todo expandido: 129 cajas).
- Funciones comprobadas por script: 8 campos en el panel y en la fila de la tabla; ordenar (asc/desc) por ubicación; copiar ruta:línea (se leyó el portapapeles); filtro de texto y de nivel; exportar CSV (61 líneas con 60 hallazgos) y JSON (60); enlace permanente (recarga y reabre el hallazgo); pestaña de agente B (2 niveles, sin Hipótesis); teclado en el grafo (Tab, flechas, Enter, Esc) y atajo `t`.
- Rendimiento (tiempo de render dentro de la página, 300 hallazgos del primer agente, escritorio): grafo agrupado 102 ms, tabla (100 filas) 90 ms, impresión (300 filas y 93 detalles) 113 ms; expandir todas las carpetas (129 cajas, 302 aristas) unos 300 ms. Con carga y primer render hasta unas 3 veces más en móvil emulado (grafo 184 ms, que aquí cae a lista).

## 5. Lo que NO verifiqué

- Lector de pantalla real (NVDA/JAWS/VoiceOver): solo razoné la estructura (pestañas con roles, `aria-sort`, `aria-expanded`, `<details>`, roving tabindex, contadores con `aria-live`).
- Safari y Firefox; solo Edge (Chromium). El respaldo sin `backdrop-filter` y `prefers-contrast` están escritos pero no los probé forzando la falta de soporte. `brightness()` dentro de `backdrop-filter` en otros motores: no probado.
- Rendimiento en un teléfono real (solo emulación de ventana).
- Daltonismo con simulador (niveles por forma, borde e icono, no probado con simulador).
- Contraste de iconos y bordes 3:1 solo a ojo; no medí estados atenuados (cajas fuera del camino seleccionado, que se atenúan a propósito) ni foco.
- La impresión real desde el diálogo del navegador (solo emulación y PDF de Edge); no vi el PDF página por página.
- Snyk, y las partes marcadas "NO verificado" de la tabla de fuentes; no abrí SonarQube ni Semgrep directamente.
- Más de 300 hallazgos, o más de 14 grupos de carpeta con rutas muy profundas; con cientos de efectos distintos la columna Efecto crecería (no hay agrupación de efectos).
- El orden de cajas reduce cruces con un promedio simple (baricentro); con 300 caminos las líneas entre Dónde y Qué es se amontonan (se reduce con grosor y opacidad, no se elimina). El grafo agrupado es un panorama, la tabla es la vista de trabajo.

## 6. Decisiones para Alex

1. ¿El cristal oscuro "más de revista" (tinte más bajo, más color dentro del panel) a costa de bajar el contraste de textos grises, o se queda el equilibrio actual (contraste 4.5:1 cumplido, efecto visible sobre todo en bordes, anillos y zonas sin texto)?
2. ¿Con más de 60 hallazgos abre en Tabla (hoy) o siempre en Grafo?
3. ¿El ID estable `AR-xxxxxx` se acepta como identificador (hash de agente, tipo, ruta y línea) o se prefiere un GUID guardado por AgentReach para poder comparar ejecuciones en la fase 2?
4. Print: con más de 60 hallazgos imprime el detalle solo de los Comprobados. ¿Se prefiere imprimir todos (cientos de páginas) o un conmutador?
5. Los niveles de cada agente: ¿los significados por agente (hoy un texto distinto por nivel y agente) salen del reporte real de cada agente, o AgentReach los define de forma central?
6. ¿Se añade la agrupación de la columna Efecto (por servicio) y el mini-mapa si el grafo con 300 se usa de verdad? Hoy basta el resumen lateral.
7. Exportar y copiar enlace son acciones del usuario (descarga y portapapeles); no guardan nada en el navegador. ¿Se acepta que el `#` de la dirección anote agente, tamaño y hallazgo?
8. El tema claro se conserva con cristal blanco; ¿se alinea con la barra oscura de marca como sugiere `colores.md`?
