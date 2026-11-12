
## Deferred from: code review de las historias 9 a 11 (2026-11-10)

- [Review][Defer] opencode no revisa los agentes `.md` globales (`~/.config/opencode/agent(s)`), solo `.opencode/` del proyecto [opencode/__init__.py:_agentes_con_permisos] — severidad media SIN VERIFICAR; lo que lo resolveria: confirmar en la documentacion de opencode que esa carpeta global se carga y que un agente ahi con `permission`/`tools` cambia lo que puede leer.

- source_spec: spec-historia-29-colores-legibles-en-cualquier-terminal.md
  summary: Historia 30 (Story 5.7): todo lo que imprime la CLI (bienvenida, las dos preguntas de permiso, avisos y "reporte guardado en") pasa por el ajuste de ancho y no parte palabras.
  evidence: Dividida de la Historia 29 por el estandar de una sola meta por spec; se construye justo despues, en una segunda pasada (Alex pidio las dos, en ese orden). Origen: en Orca se vio "Solo g / uarda".

- source_spec: spec-historia-29-colores-legibles-en-cualquier-terminal.md
  summary: Historia 31 (por escribir): detectar el color de fondo real de la terminal (consulta OSC 11) para que el logo y el cuerpo del reporte se adapten a CUALQUIER fondo, no solo claro/oscuro.
  evidence: Fuera de la 29 porque exige leer la entrada de la terminal (choca con FR-30 y con la Story 7.4/M1) y no se puede verificar sin una terminal real. Primero Alex prueba con una sonda si Orca responde a la consulta; si no responde, se queda el caso "desconocido".
- source_spec: spec-historia-29-colores-legibles-en-cualquier-terminal.md
  summary: Colores del CUERPO del reporte (comprobado, potencial, etc.) cuando el tema es desconocido y la terminal es de 24 bits sobre fondo claro (p. ej. el ambar sobre blanco da 1,9:1).
  evidence: La 29 solo corrige el logo para no cambiar el aspecto del reporte en las terminales oscuras, que son la mayoria; el cuerpo se resuelve mejor con la deteccion real del fondo (Historia 31).

- source_spec: spec-historia-30-todo-lo-impreso-respeta-el-ancho.md
  summary: Una ruta con espacios (p. ej. «Program Files») puede partirse entre palabras en la pregunta de permiso y en «guardado en» cuando es mas larga que el ancho.
  evidence: El ajuste parte por espacios; protegerla exige reconocer que una linea es una ruta. Es legible pero no se puede copiar de un tiron. Se resuelve junto con la Historia 31 o con un marcador de ruta en los textos.

- source_spec: spec-historia-32-la-terminal-explica-cada-termino.md
  summary: Historia 33 (Story 6.5): seccion plegable «Como leer este reporte» en el HTML con las 11 fichas, un ejemplo por nivel, enlace «¿que es esto?» junto a cada termino, y retirar el «usted» fijo de la plantilla (que siga el tono elegido).
  evidence: Dividida de la Historia 32 por el estandar de una sola meta; reutiliza el catalogo de terminos que crea la 32. Fuente de diseño: ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md.
- source_spec: spec-historia-32-la-terminal-explica-cada-termino.md
  summary: Historia 34 (Story 6.6): el README (en ingles) define los mismos 11 terminos con el mismo sentido, con una prueba que compara el catalogo con el README.
  evidence: Dividida de la Historia 32; depende del catalogo de la 32. README unico en ingles (decision de Alex 2026-11-09).

- source_spec: spec-historia-32-la-terminal-explica-cada-termino.md
  summary: Tres terminos (sandbox, «no se pudo revisar» y «codigo de salida») tienen linea de terminal en el catalogo pero no se imprimen en el resumen; solo salen con --detalle.
  evidence: Consecuencia del tope de 12 lineas fijado en la spec; subirlo unas 3 lineas los explicaria. Decision de Alex pendiente (recomendacion: dejarlo corto).
- source_spec: spec-historia-32-la-terminal-explica-cada-termino.md
  summary: Comprobar que los terminos explicados con --detalle incluyen siempre los del resumen (y al reves no sobran), con una prueba que comparta el calculo de _presentes y de las secciones.
  evidence: Hallazgo de casos limite sin verificar (maybe-false, medium): _presentes y las secciones calculan las causas por separado.
- source_spec: spec-historia-32-la-terminal-explica-cada-termino.md
  summary: Investigar por que home-falso/.npmrc pierde la linea citada y la autocomprobacion lo corrige («el archivo cambio o ya no coincide», pero el archivo no cambio).
  evidence: Visto en la salida real tras la Historia 32 (ahora el aviso dice cual hallazgo): credencial en un archivo, home-falso/.npmrc. Puede ser un fallo del reabrir-y-confirmar la linea en .npmrc o un mensaje impreciso.

- source_spec: spec-historia-33-como-leer-este-reporte-en-el-html.md
  summary: Historia 35: el resto de los textos propios de la plantilla HTML (los diccionarios es de la plantilla, hoy con «usted» fijo) siguen el tono elegido (tu o usted) como el glosario nuevo.
  evidence: Dividida de la Historia 33 por el estandar de una sola meta; la 33 solo hace que la seccion nueva siga el tono. Contrato de UX: «todos los textos propios del HTML siguen el tono elegido».

- source_spec: spec-historia-33-como-leer-este-reporte-en-el-html.md
  summary: Historia 36: enlace «¿que es esto?» junto a cada termino del reporte HTML que abre y lleva a su ficha en «Como leer este reporte» (hoy cada ficha ya tiene id term-… pero nada la enlaza), con foco y lector de pantalla.
  evidence: Descrito en el contrato de UX (EXPERIENCE.md) y fuera de la spec de la 33; Alex lo veria util para gestionar lo que lee.
