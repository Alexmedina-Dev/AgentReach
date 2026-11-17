# Epic 4 Context: Entender el resultado de un vistazo

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

La persona lee el resultado de una auditoría en la terminal y en el navegador, en español o inglés, con color accesible, `doctor` y un flujo diario corto, en cualquier terminal (claro, oscuro o de fondo desconocido). Las historias base (4.1 a 4.7) están terminadas; la 4.10 está implementada y en revisión; quedan pendientes detectar el color de fondo real, marcar hallazgos repetidos entre agentes, que los filtros de nivel del HTML digan cuál está activo y avisar cuando la carpeta revisada contiene varios proyectos.

## Stories

- Story 4.1: Reporte con ocho campos, idiomas, orden, autocomprobación y código de salida (terminada)
- Story 4.2: Reporte de terminal: ancho, color, codificación y limpieza (terminada)
- Story 4.3: Marca, `doctor`, tema y tono (terminada)
- Story 4.4: Reporte HTML estático (terminada)
- Story 4.5: Diseño final del reporte HTML (terminada)
- Story 4.6: Uso diario (terminada)
- Story 4.7: Colores legibles en cualquier terminal (terminada)
- Story 4.8: Detectar el color de fondo real de la terminal (pendiente)
- Story 4.9: Un mismo archivo y línea que sale en varios agentes lo dice (pendiente)
- Story 4.10: Se ve que AgentReach avanza mientras revisa (implementada, en revisión)
- Story 4.11: Los filtros de nivel dicen cuál está activo y qué muestran (pendiente)
- Story 4.12: Aviso cuando la carpeta revisada contiene varios proyectos (pendiente)

## Requirements & Constraints

- Cada hallazgo se muestra con ocho campos y evidencia reproducible (archivo y línea); la explicación sale de catálogos fijos, bilingües, sin modelo de lenguaje.
- Hay un reporte (o sección) por agente; no se colapsa nada entre agentes.
- Cobertura y límites declarados: un reporte vacío nunca se lee como «seguro»; nunca se dice «seguro» ni «sin riesgo».
- La autocomprobación corrige hacia abajo antes de imprimir y dice cuál hallazgo cambió.
- Terminal legible en Windows: ancho, color, codificación, idioma, tono (tú/usted), banner, `doctor`, tema. El color nunca es la única señal (símbolo y palabra siempre).
- Todo texto con contraste mínimo de 4,5:1 (3:1 en las letras grandes del logo) contra blanco y negro cuando el tema es desconocido.
- HTML estático, un solo archivo, sin red ni recursos externos, por agente, en dos idiomas, con vista Recorrido.
- Salida determinista: mismo proyecto, mismos hallazgos y mismo orden.
- Nada de lo nuevo puede escribir archivos, usar red, ejecutar programas, mostrar valores de secretos ni cambiar hallazgos o niveles.
- Story 4.8: la consulta del color de fondo (OSC 11) es una exploración, no probada en Orca ni en Windows Terminal; antes de construir, probar con una sonda corta. Debe respetar el permiso de lectura por persona (no leer de la entrada sin terminal) y esperar como máximo 200 ms antes de caer a colores neutros. Si no funciona, bastan las demás capas.
- Story 4.9: la marca «también en: <agente>» (inglés «also in») exige misma ubicación (archivo y línea) y mismo tipo; cada hallazgo conserva su nivel y su conteo por agente; la marca lleva solo el nombre del agente; sale en español (tú y usted) e inglés; una prueba con el caso de `.env` (Claude Code y opencode) la protege. Un reporte de un solo agente no lleva marca.
- Story 4.10: el avance sale por la salida de errores y solo con terminal interactiva; nunca en el reporte, `--salida`, redirección, `TERM=dumb`, modo de pruebas ni HTML. Una sola línea que se actualiza en su sitio (fase, pasos, carpetas y tiempo; sin porcentaje de archivos porque el total no se conoce de antemano). No muestra nombres de archivo ni valores (la prueba canario lo verifica). Se borra al terminar y Ctrl+C sale limpio con código 130. Falta su comprobación manual en una terminal real.
- Story 4.11: las fichas de nivel activas se rellenan con el tinte de su nivel y llevan una marca que no es solo color; las apagadas se ven apagadas y sin tachar, con `aria-pressed`; «Caminos» se ve como total, no como botón; una línea dice qué niveles y cuántos caminos se muestran (ES tú/usted, EN), incluido el caso de ninguno. Los demás grupos de selección (pestañas de agente, vistas, idioma, tema) distinguen el estado seleccionado con contraste 3:1 sin depender solo del color, en tema claro, oscuro y contraste alto.
- Story 4.12: se avisa cuando 2 o más carpetas dentro de la revisada (no ella misma) tienen su propio punto de partida (`.git/config`, `.claude/settings.json`, `.claude/settings.local.json`, `CLAUDE.md`, `opencode.json`, `opencode.jsonc`, `.opencode/opencode.json`), usando solo los archivos que el recorrido ya vio, sin recorridos nuevos ni IA. Se ignoran carpetas internas de herramientas (`.git`, `node_modules`, `.claude`, `.opencode`); los `package.json` no cuentan (un monorepo no dispara el aviso). El aviso sale arriba, antes de los hallazgos, en terminal y HTML, en ES (tú/usted) e inglés; dice cuántas carpetas son, sin nombres ni rutas, y sugiere revisar un proyecto a la vez. No es un hallazgo: no cambia niveles, conteos ni código de salida.

## Technical Decisions

- Arquitectura hexagonal con tubería de filtros: el núcleo (`core/`) solo importa `contracts/`; texto y HTML pertenecen a `reporting/` y reciben vistas ya filtradas, nunca un `Finding` crudo.
- Compuerta única (`gate.preparar`) construye `HallazgoVista` y `DatosReporte` congelados con lista blanca de campos; cualquier dato nuevo para el reporte (la marca de coincidencia entre agentes de 4.9, el aviso de varios proyectos de 4.12) debe pasar por ahí.
- Un solo punto de ajuste del texto impreso (`_texto` y `formato.ajustar`): ancho de trabajo acotado a 60-100 columnas, partir solo en límites de palabra, medir ancho visible. Todo texto nuevo, incluidos el avance y el aviso, debe pasar por él.
- Color decidido por `--color` > `NO_COLOR` > no es terminal o `TERM=dumb` > soporte de Windows. Tema de tres estados con prioridad `--tema` > `AGENTREACH_TEMA` > `COLORFGBG` > desconocido; con desconocido, AGENT usa el color normal del texto y REACH un menta-teal legible. El logo solo se dibuja si cabe y no hay redirección, `NO_COLOR`, `--no-banner` ni `--salida`.
- Un solo catálogo de términos (12 fichas, tono tú/usted, ES/EN) alimenta terminal, HTML y README; nadie redefine un término en su salida.
- HTML: el marcador `__AGENTREACH_DATA__` de la plantilla se reemplaza por JSON compacto escapado; el HTML no inventa textos (el glosario y los textos de la línea de estado de filtros van en los datos); topes de 20 MB y 20 000 hallazgos por agente. Esquema en `docs/reporte-html/`.
- Códigos de salida: 0, 1 (hay comprobados, o no revisados con `--estricto`), 2 (uso o permiso), 3 (error interno), 130 (Ctrl+C).
- Cero dependencias de ejecución (solo biblioteca estándar), Python 3.12+. Las únicas escrituras permitidas están en `cli/__init__.py` y `cli/reportes.py`; una prueba estática lo impone, así que el avance de 4.10 no puede escribir archivos.
- Convenciones: módulos y funciones en español sin tildes; un archivo de pruebas por historia o área; las pruebas de `reglas_no_negociables/` y del oráculo son bloqueantes.

## UX & Interaction Patterns

- Orden de la terminal: banner, encabezado, resumen por nivel, agentes configurados, por qué hay «no determinado», lo más urgente (tres hallazgos con línea «qué hacer»), alcance, cierre. La terminal es corta; `--detalle` da el listado completo. El aviso de varios proyectos (4.12) va arriba, antes de los hallazgos.
- Una frase por término (máximo 90 caracteres), solo donde la jerga aparece; sin identificadores técnicos sin su explicación al lado.
- HTML: «Cómo leer este reporte» primero y abierto; enlace «¿qué es esto?» junto a cada término; funciona sin JavaScript; foco visible, `lang` correcto, sin animación necesaria.
- Filtros del HTML (4.11): estado activo visible por tinte, marca y texto, nunca solo color; una línea tipo «Mostrando 5 caminos: Potencial» siempre refleja el filtro vigente.
- Reglas de voz: lenguaje llano, sin emojis, nunca «seguro», «potencial» nunca se presenta como menor, jamás un valor de secreto.
- Estados: sin color (símbolo y palabra bastan, sin banner), ASCII con respaldo `[!!] [!] [?] [-]`, ancho angosto (bajo 60 se trabaja a 60; bajo 40, banner mínimo ASCII).
- Logo (4.7 y 4.8): REACH conserva el tono menta y ajusta solo su luminosidad hasta 3:1; AGENT usa el neutro de mayor contraste; con fondo desconocido, ambos heredan la paleta del tema del usuario. Nunca se pinta el fondo.
- Avance (4.10): una línea viva, sin animación que oculte un bloqueo real, y el reporte no debe contener restos.

## Cross-Story Dependencies

- 4.8 depende de 4.7 y de la política de permiso de lectura (no leer de la entrada sin terminal; Story 7.4 sobre la respuesta desde el teclado físico).
- 4.9 depende de 4.4 (HTML) y del formato de la compuerta; debe respetar la regla de un reporte por agente.
- 4.10 depende de 4.2 (ancho y color de la terminal) y comparte la regla de que ningún texto sale sin pasar por el ajuste de ancho.
- 4.11 depende de 4.5 (diseño final del HTML); toca la misma plantilla HTML que 4.9 y 4.12, así que conviene coordinar los cambios en ella.
- 4.12 depende de 4.4 (HTML) y de la terminal de 4.2; reutiliza la compuerta y la lista de archivos ya recorridos, y comparte plantilla con 4.9 y 4.11.
- La Story 7.4 (confirmación desde la terminal real) condiciona cualquier lectura de respuestas de la terminal.
