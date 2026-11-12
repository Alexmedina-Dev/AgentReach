# Reporte HTML: esquema de datos (versión 1)

Qué es esto: la forma exacta de los datos que el generador de Python (biblioteca estándar) pone dentro de `plantilla.html`. JSON es un formato de texto para guardar datos (llaves, listas y textos entre comillas); el esquema formal, para validarlo, está en `esquema-datos.schema.json`. Un ejemplo ficticio completo está en `datos-demo.json` (60 hallazgos de Claude Code, 10 de opencode y 2 sin agente específico).

## Cómo entra el dato en la plantilla

- La plantilla tiene un único bloque `<script type="application/json" id="data">__AGENTREACH_DATA__</script>`. El marcador `__AGENTREACH_DATA__` aparece **una sola vez** en todo el archivo (en el código se escribe partido en dos trozos a propósito). El generador reemplaza ese marcador por el JSON y no toca nada más.
- Antes de reemplazar: `json.dumps(datos, ensure_ascii=False, separators=(",", ":"))` y después cada `<` se escribe `<` (también U+2028 y U+2029). Así un `</script>` o un `<!--` dentro de un nombre de archivo no puede cerrar el bloque. Dentro de un texto JSON, `<` vuelve a ser `<` al leerlo, y la plantilla lo muestra siempre como texto, nunca como HTML.
- Si el marcador sigue ahí (la plantilla sin datos), la página lo dice en vez de romperse.
- Un solo archivo: sin fuentes, scripts, imágenes ni hojas de estilo externas. La plantilla lleva una política de contenido (`Content-Security-Policy`: lista de lo que el navegador deja cargar) con `default-src 'none'`, por lo que aunque hubiera un error el navegador no pediría nada a la red.

## Idiomas

Todo texto para personas viaja como `{"en": "...", "es": "..."}`. La plantilla trae los botones EN y ES y cambia sin volver a generar. Los textos salen de los catálogos fijos (`core/catalogo_explicaciones.py` y `contracts/finding.py`); no se usa ningún modelo de lenguaje. El tono del español es el "cercano" (de tú) del reporte de terminal; si la historia 13c añade el tono formal, el generador elige cuál catálogo vuelca (la plantilla no cambia).

## Forma general

```
schema_version      1
tool, tool_version  "AgentReach", "0.1.0"
initial_language   "en" o "es" (opcional): el idioma con que abre el archivo (`--idioma`); el lector puede cambiarlo
configured_agents   (opcional) agentes con archivos de configuración en disco: [{id: "claude_code"|"opencode", name, evidence:[{scope: "project"|"user"|"managed", path}]}]. Se muestra como «configurado», NUNCA «ejecutado»: AgentReach vio archivos, no sabe si el agente corrió. La evidencia son rutas, sin contenido.
agents[].not_determined   (opcional) por qué hay hallazgos con nivel «no determinado»: [{path, key, reason}]: el archivo y la CLAVE de configuración que AgentReach no interpreta (p. ej. `hooks.PreToolUse`), nunca un valor. La plantilla lo agrega al «por qué» de cada hallazgo no determinado y a las exportaciones JSON y CSV (`not_determined_by`).
generated_at        texto de la fecha y hora (reloj inyectado, parámetro `ahora`)
folder              carpeta auditada, ya "visible" (ver Seguridad)
files_looked_at     archivos mirados (DatosReporte.archivos_mirados)
secrets_notice      {en, es}: "No se muestran valores de secretos..." (el texto fijo del reporte de terminal)
agents[]            una entrada por agente (ver abajo). Nunca se mezclan niveles entre agentes.
catalog             textos fijos por clave (ver abajo)
not_reviewed[]      {path, reason}: lo que no se pudo revisar
limits              {en: [6 textos], es: [6 textos]}: los seis límites fijos (LIMITES)
limits_also         {en, es}: la frase "Tampoco se revisan..." (LIMITES_TAMBIEN)
glossary           (opcional, Historia 33) los textos de «Cómo leer este reporte»: {labels: {what_is, means, to_do} (cada uno {en, es}: «Qué es», «Qué significa para ti/usted», «Qué puedes/puede hacer»), terms: [{id, name, line, what_is, means, to_do}]} con las 12 fichas de `core/catalogo_terminos.py` (cada texto {en, es}; el español con el tono elegido). Sin valores ni rutas.
```

### `agents[]` (campo "plataforma y agente")

Reglas de reparto, iguales a `reporting/texto.py::_secciones`:

| `id` | De dónde sale | `name` |
|---|---|---|
| `claude_code` | hallazgos con `Plataforma.CLAUDE_CODE` | `"Claude Code"` |
| `opencode` | hallazgos con `Plataforma.OPENCODE` | `"opencode"` |
| `none` | hallazgos con `Plataforma.NO_DETERMINADA` (no atados a un agente) | `{"en": "Not tied to a specific agent", "es": "Sin agente específico"}` |

La plantilla muestra un selector con un botón por entrada ("Claude Code (12)", "opencode (3)"). Cada botón muestra **sus** niveles, su radar, sus reglas y sus hallazgos; no existe la vista "todos mezclados". Con `--agente`, el generador solo incluye ese agente (como ya hace `gate.preparar`). Un agente sin hallazgos igual aparece, con la frase "no tiene hallazgos, eso no significa que no pueda hacer daño". La entrada `none` solo se incluye si tiene hallazgos.

Cada entrada: `{id, name, env_cleaning, rules[], findings[]}`.

- `env_cleaning`: `DatosReporte.limpieza_de_entorno` contiene esa plataforma.
- `rules[]`: de `DatosReporte.reglas` (`ReglaVista`): `{posture, tool, location}` con `posture` en `allow|ask|deny|no_determinada`, `tool` = `ReglaVista.herramienta` (ya escrita sin peligros) y `location` = `ReglaVista.ubicacion` (`archivo:línea`). Son contexto, no hallazgos.

### `findings[]` (los ocho campos del PRD, FR-9)

| Campo del hallazgo real | Clave en el JSON | Notas |
|---|---|---|
| (1) ubicación: ruta | `path` | `HallazgoVista.ruta` (relativa a la carpeta, con `/`, peligros escritos). Nunca `ruta_real`. |
| (1) ubicación: línea | `line` | entero >= 1, o `null` cuando es `Linea.NO_DETERMINADA` (`HallazgoVista.linea is None`). Nunca 0 ni un número inventado. La plantilla escribe "línea no determinada" / "line not determined". |
| (2) qué es | `type` | código `"TH-1"` a `"TH-20"` (`Tipo.value`); el título corto sale de `catalog.types[type].title` (`TITULO_TIPO`). El código `TH-n` no se muestra en pantalla (como el reporte de terminal sin `--detalle`), solo sirve de clave y de búsqueda. |
| (2) de quién | `provider` | `Proveedor.value`; texto en `catalog.providers` (`PROVEEDOR`; `no_aplica` sale vacío y la plantilla no escribe nada). |
| (3) nivel | `level` | `comprobado`->`verified`, `potencial`->`potential`, `hipotesis`->`hypothesis`. Los nombres (Comprobado/Verified...) y su frase los lleva la plantilla. |
| (3) por qué | `reason` | `Motivo.value`; texto en `catalog.reasons` (`texto_de_motivo`, los dos idiomas). |
| (4) ajeno a la tarea | `unrelated` | `si`, `no` o `no_determinado` (`Ajeno.value`); texto en `catalog.unrelated` (`AJENO`). |
| (5) plataforma | (la entrada `agents[]` que lo contiene) | `HallazgoVista.plataforma`. |
| (5) agente | `agent` | `HallazgoVista.agente` (etiqueta corta: letras, números, `.`, `-`, `_`) o `null`. |
| (6) reglas del agente: postura | `posture` | `allow`, `ask`, `deny`, `sin_regla`, `no_determinada`; texto en `catalog.postures` (`POSTURA`). |
| (6) reglas del agente: archivo y línea | `rule` | `HallazgoVista.regla` (`"archivo:línea"` visible) o `null`. |
| (7) qué hacer | `text` -> `catalog.texts[text].what_to_do` | `que_hacer(tipo, idioma, tono)`. |
| (8) qué significa | `text` -> `catalog.texts[text].meaning` | `que_significa(tipo, ajeno, idioma, tono)`. `text` es el código del tipo; para TH-17 es `"TH-17/si"` o `"TH-17/no_determinado"` porque su texto cambia con "ajeno a la tarea" (con `no` sirve `"TH-17"`). |
| fuente verificada | `source_verified` | `HallazgoVista.fuente_verificada`; hoy solo informativo. |
| (identificador) | `id` | consecutivo por agente (`cc-0`, `cc-1`...); lo usa la plantilla para enlazar. No viene del contenido de ningún archivo. |

Por qué un catálogo aparte y no los textos dentro de cada hallazgo: con cientos de hallazgos del mismo tipo, repetir las explicaciones multiplicaría el tamaño del archivo (con este catálogo, un reporte de prueba con 340 hallazgos ocupó unos 120 KB en total). El generador solo vuelca las entradas del catálogo que se usan (no los 20 tipos si solo hay 3).

### `not_reviewed[]` ("qué no pudo revisar AgentReach", parte A)

`{path, reason}` con `reason` = `MotivoNoRevisado.value` (lista cerrada de 10). Los textos van en `catalog.no_review[reason]` = `{title, how_to_fix}` (`TITULO_MOTIVO` y `COMO_RESOLVER`). Se repite una vez por ruta (igual que la compuerta, que quita duplicados). La plantilla agrupa por motivo y escribe el "cómo resolverlo" una sola vez por grupo. Esta sección no es por agente: un archivo que no se leyó no pertenece a un agente.

### `limits` y `limits_also` (parte B, límites fijos)

Los seis textos de `LIMITES[idioma]` y la frase de `LIMITES_TAMBIEN[idioma]`, siempre presentes aunque no haya hallazgos (como en el reporte de terminal).

## Qué decide la plantilla (no el generador)

- Qué ve el lector según la cantidad: pocos hallazgos (6 o menos): tarjetas anchas a todo el ancho; de 7 a 24: tarjetas en dos columnas; más de 24: grupos plegados por nivel (el de comprobados abierto) con filas que se abren y "mostrar 40 más"; más de 60 por agente: arranca en vista de tabla. Todo se puede cambiar con el botón Tarjetas/Tabla.
- Tabla ordenable por nivel, archivo, tipo y agente, con "Copiar" (copia `ruta:línea`, o solo la ruta si la línea no se determinó) y "Detalle" que abre los ocho campos. Se pagina de 100 en 100.
- Impresión: al imprimir (o con el botón Imprimir) se arma una versión de papel con **todos** los agentes y **todos** los hallazgos en una tabla simple, blanco y negro, con los ocho campos; no sale la aurora ni los botones.

## Reglas de seguridad (obligatorias para el generador)

1. **Nunca un valor de secreto.** El JSON solo se arma desde `DatosReporte` y sus vistas (`HallazgoVista`, `NoRevisadoVista`, `ReglaVista`), que ya no tienen dónde guardar un valor (`reporting/gate.py`). El generador no recibe un `Finding` ni lee archivos del proyecto. No se vuelca nada que no esté en este esquema (`additionalProperties: false`).
2. **Ruta limpia de caracteres de control.** Todo texto que viene de un archivo del usuario (`path`, `rule`, `rules[].tool`, `rules[].location`, `folder`, `not_reviewed[].path`) pasa por `reporting/limpieza.py::escribir_peligrosos`: los caracteres de control, de dirección (U+202E), invisibles y sustitutos salen **escritos** (`\x1b`, `‮`), no borrados. Nunca se usa `ruta_real`. La plantilla repite esta limpieza (segunda barrera) y además escribe así cualquier carácter peligroso que encuentre en cualquier texto.
3. **Tamaño máximo.** Cada ruta o nombre: 1000 caracteres, con la marca `...[recortada: N caracteres]` (`MAX_NOMBRE`). Hasta 20 000 hallazgos por agente y 20 000 entradas no revisadas (el esquema lo fija). El archivo final no pasa de 20 MB; si lo pasaría, el generador no escribe un reporte parcial: termina con el código de salida 3 y un mensaje (mismo criterio que la Historia 13: no se muestra un reporte parcial). La plantilla recorta por su cuenta cualquier texto de más de 1000 caracteres y pagina las listas largas, así que un archivo grande no congela la página.
4. **La plantilla nunca usa HTML crudo de los datos.** Todo texto se escapa (`& < > " ' ` `) antes de entrar al HTML; los datos no se usan en atributos sin escapar ni en `href`, `src`, `style` ni en manejadores de eventos. No hay `eval`, ni `document.write`.
5. **Escritura segura del archivo.** `--salida` escribe UTF-8, rechaza una ruta dentro del proyecto auditado (igual que el reporte de terminal) y no sigue enlaces simbólicos al crearlo.
6. **Cero red.** Sin recursos externos y con política de contenido que prohíbe cargarlos. Una prueba lo comprueba con el texto del archivo generado.

## Cosas que NO cambian el esquema pero conviene saber

- El esquema valida forma y tamaños, no puede comprobar que una ruta esté "limpia": eso lo prueba el generador (prueba con nombres con `ESC[2J`, U+202E y `</script>`).
- Si en el futuro hay más agentes que Claude Code y opencode, se añade un `id` nuevo; la plantilla ya muestra un botón por entrada de `agents[]`. Hoy el esquema permite hasta 8.
- `schema_version` sube cuando cambia la forma; la plantilla de una versión no lee datos de otra.
