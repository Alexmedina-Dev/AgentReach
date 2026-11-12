---
title: 'Historia 33: «Cómo leer este reporte» va primero y siempre visible en el HTML'
type: 'feature'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
baseline_commit: 'b4c47638770eb8394d590df0f426000f754cfdcb'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-6-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Quien termina la revisión en la terminal y abre el reporte HTML ve «Comprobado», «Potencial», «Hipótesis» y los caminos, pero no sabe qué significa cada uno: el HTML solo trae una leyenda de una línea dentro del reporte y los caminos no se explican en ningún lugar. Además, en inglés «path» ya significa ruta de archivo y confunde.

**Approach:** Una sección «Cómo leer este reporte» / «How to read this report», lo **primero** del HTML después de la cabecera, **abierta por defecto** (se puede plegar), con el significado completo de los tres niveles y del camino de alcance y, plegados, los demás términos del catálogo de la Historia 32. Sus textos viajan en los datos del reporte (con el tono elegido para el español), no escritos a mano en la plantilla. Se aplica la nomenclatura inglesa acordada por Alex.

## Boundaries & Constraints

**Always:** Solo biblioteca estándar; el HTML sigue siendo un único archivo estático, sin recursos externos ni scripts externos (`default-src 'none'`). Los textos salen del catálogo de términos (`core/catalogo_terminos.py`), ES (tú o usted según `--tono`) e inglés; el cambio de idioma de la página los cambia. Nunca «seguro», «sin riesgo» ni «lo seguro que es»: se dice «con qué firmeza lo sabemos». En español el nivel es «Comprobado»; en inglés, «Verified». Nomenclatura: español **Camino de alcance** y **Recorrido** (sin cambio); inglés **Reach route(s)** para el camino (hoy «Path/Paths») y **Route map** para la vista (hoy «Route»); «path» queda solo para rutas de archivo (por ejemplo «Copy path:line»). Accesible: encabezado con `aria-labelledby`, plegado nativo con `<details>`, contraste de los tokens existentes, y se incluye abierta al imprimir. Si se cambia `plantilla_reporte.html`, se cambia igual su copia `docs/reporte-html/plantilla.html` (una prueba las compara) y el esquema de datos (`esquema-datos.md` y `.schema.json`) con un campo aditivo y opcional.

**Never:** Cambiar los textos de la terminal (Historia 32), el cálculo de niveles, el oráculo ni los códigos de salida. Escribir valores de secretos. Reescribir ahora los demás textos propios de la plantilla que hoy usan «usted» fijo (queda como historia aparte). Añadir dependencias.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Orden y estado | Cualquier reporte, con o sin hallazgos | La sección es el primer bloque tras la cabecera y está abierta (`open`) | N/A |
| Niveles | Español tú, español usted, inglés | Define Comprobado/Potencial/Hipótesis (Verified/Potential/Hypothesis) con el significado completo de las fichas 1 a 3 | N/A |
| Camino de alcance | Cualquier reporte | Explica Agente → Dónde → Qué hay → Efecto posible y la línea continua (comprobado) y discontinua (no comprobado) | N/A |
| Otros términos | Los demás términos del catálogo | Plegados dentro de la sección, cada uno con qué es, qué significa y qué puedes hacer | Término sin entrada: la prueba de cobertura falla |
| Cambio de idioma | El usuario cambia ES/EN en la página | La sección cambia de idioma sin recargar | N/A |
| Tono | `--tono formal` | El español usa «usted» en la sección; el inglés no cambia | N/A |
| Nomenclatura inglesa | Página en inglés | Dice «Reach route(s)» y «Route map»; no usa «path(s)» para el camino | Una cadena en inglés que aún diga «path» para el camino hace fallar la prueba |
| Imprimir | Vista Imprimir | La sección sale abierta | N/A |
| Seguridad | Reporte con valores canario | Ningún canario en el HTML; sin recursos externos | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/reporting/plantilla_reporte.html` (copia idéntica en `docs/reporte-html/plantilla.html`) -- diccionarios de idioma `T_` en línea (en ~l.708-745, es ~l.750-790): etiquetas del camino (`total`, `modePaths`, `panelTitle`, `panelHint`, `through`, `step`, `skip`…) y de la vista (`graph:'Route'` / `graph:'Recorrido'`); estructura: cabecera `#top` (~l.512), aviso (~l.546), `#cfg` (~l.549), pestañas, `#summary` (~l.557), vistas; `<details class="fold">` ya existe como patrón plegable; leyenda actual de niveles `ul.lvlegend` (~l.1011, `LV_MEAN` ~l.650).
- `src/agentreach/reporting/html.py` -- `construir_datos` (~l.170), `_catalogo` (~l.146) y `_i18n` (~l.154): así viajan los textos por hallazgo en ES y EN con el tono aplicado; el glosario viaja igual en un campo nuevo (por ejemplo `glossary`).
- `src/agentreach/core/catalogo_terminos.py` -- las 11 fichas (línea de terminal y explicación larga en tú, usted e inglés); aquí se ajustan las fichas 1 y 2 y se añade la ficha 12 «camino de alcance».
- `docs/reporte-html/esquema-datos.md` y `esquema-datos.schema.json` -- esquema cerrado v1; añadir el campo aditivo.
- `README.md` -- sección «Reach paths» (~l.122-128): renombrar a «Reach routes» y sus menciones.
- `_bmad-output/planning-artifacts/ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md` -- contrato: dejar las fichas 1, 2 y 12 con el mismo texto que el catálogo.
- `tests/test_reporte_html.py` -- pruebas existentes del HTML (esquema, canarios, sin recursos externos, determinismo, copia de la plantilla); deben seguir pasando.

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/core/catalogo_terminos.py` -- ficha 1 «Comprobado»: añadir al «Qué es» «El permiso se calcula con los datos que guarda el sistema sobre quién puede leer el archivo, sin abrirlo para probarlo.»; ficha 2 «Potencial»: añadir «Por ejemplo, no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, no una barrera real del sistema.»; ficha 12 nueva «Camino de alcance» (texto abajo); las tres variantes de cada una -- fuente única de los textos
- [ ] `src/agentreach/reporting/html.py` -- incluir el glosario (las 12 fichas, ES con el tono elegido e inglés) en los datos, con el esquema actualizado -- los textos viajan en los datos
- [ ] `src/agentreach/reporting/plantilla_reporte.html` y `docs/reporte-html/plantilla.html` -- sección «Cómo leer este reporte» primero y abierta (niveles y camino a la vista, el resto plegado), cambio de idioma, impresión, y la nomenclatura inglesa -- la experiencia
- [ ] `README.md` -- «Reach paths» pasa a «Reach routes» -- misma nomenclatura
- [ ] `EXPERIENCE.md` -- sincronizar fichas 1, 2 y 12 -- el contrato manda
- [ ] `tests/test_historia_33.py` -- cada fila de la matriz; cobertura de las 12 fichas × 3 variantes en el HTML; orden (la sección va antes de `#summary`) y `open`; ausencia de «seguro»; esquema válido; copia idéntica de la plantilla; en inglés ninguna etiqueta del camino dice «path» -- cubre la matriz
- [ ] `_bmad-output/implementation-artifacts/spec-historia-33-*.md` e `historias-mvp.md` -- Estado y «no verificado»; registrar como pendiente la Historia 35 (que el resto de los textos de la plantilla siga el tono)

**Texto de la ficha 12 «Camino de alcance» (copiar tal cual)**
- *Terminal, tú/usted:* «Camino de alcance: cómo un agente llegaría de su carpeta a un efecto posible.» · *EN:* «Reach route: how an agent could get from its folder to a possible effect.»
- *HTML (tú).* *Qué es:* cada hallazgo se muestra como un camino de cuatro pasos: Agente → Dónde → Qué hay → Efecto posible. Por ejemplo: un agente → `config/deploy.env`, línea 3 → un token de la nube → podría dar acceso a una cuenta de despliegue. *Qué significa para ti:* una línea continua significa que AgentReach comprobó ese paso; una línea discontinua, que no lo comprobó: es lo que podría pasar, no algo confirmado. *Qué puedes hacer:* empieza por los caminos con el trazo continuo; en los discontinuos, comprueba a mano el paso que falta.
- *HTML (usted).* Igual, con «usted»: *Qué significa para usted:* … *Qué puede hacer:* empiece por los caminos con el trazo continuo; en los discontinuos, compruebe a mano el paso que falta.
- *HTML (EN).* *What it is:* each finding is shown as a four-step route: Agent → Where → What is there → Possible effect. For example: an agent → `config/deploy.env`, line 3 → a cloud token → it could give access to a deployment account. *What it means for you:* a solid line means AgentReach checked that step; a dashed line means it did not: it is what could happen, not something confirmed. *What you can do:* start with the routes drawn in solid line; for the dashed ones, check the missing step by hand.

**Acceptance Criteria:**
- Given cualquier reporte HTML, when se abre, then el primer bloque tras la cabecera es «Cómo leer este reporte», abierto, con los tres niveles y el camino de alcance definidos, y los demás términos plegados.
- Given la suite completa, ruff y `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan, then pasan sin omitir el oráculo.

## Implementation Notes

- Ficha 12 (`Termino.CAMINO_DE_ALCANCE`) y los textos añadidos a las fichas 1 y 2 (en inglés se tradujeron las frases del spec). `test_historia_32` pasa de 11 a 12 términos.
- `html.py::_glosario` vuelca las 12 fichas en `glossary` ({labels, terms[]}, cada texto {en, es}); esquema `.md` y `.schema.json` con el campo opcional.
- Plantilla: `<section id="howto">` primera en `.wrap`, `<details open>` que conserva lo que la persona pliega al cambiar de idioma; 4 fichas a la vista (3 niveles + camino) y 8 plegadas; `beforeprint` la abre y `afterprint` la restaura. Sin glosario en los datos la sección no sale.
- Nomenclatura inglesa: Route(s), Route map, Reach route report; «path» solo en «Copy path:line» y en rutas de archivo.
- No verificado: vista en navegador real (se probó con jsdom: sin errores, orden, open, cambio de idioma); impresión real. El enlace «¿qué es esto?» no se hizo (no está en el spec). Historia 35 registrada como pendiente.

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego | «Sin abrir el archivo» se lee como «AgentReach nunca abre tus archivos», y sí lee el contenido de archivos del proyecto para reconocer secretos | medium | patch (hecho) | El PRD FR-5 lo dice solo para probar el permiso; frase precisada en catálogo, README, contrato de UX y spec: «sin abrirlo para probarlo» |
| 2 | Brechas | El comportamiento del navegador (abierta al cargar, plegar, idioma, imprimir, sin glosario) solo se probaba con fragmentos de código | medium | patch (hecho) | `tests/test_historia_33_navegador.py` con Playwright; 4 pasan en navegador real |
| 3 | Casos límite | «Skip to the paths» sigue en el HTML estático y la prueba solo miraba el bloque `en:` | medium | patch (hecho) | Cambiado a «Skip to the routes»; la prueba escanea todo el marcado con lista de excepciones |
| 4 | Casos límite | `beforeprint` doble sin `afterprint` deja los 8 términos abiertos para siempre | low | patch (hecho) | No sobrescribe `howWas` si ya tiene datos; `afterprint` restaura solo nodos conectados |
| 5 | Ciego, casos límite y brechas | `card(x).replace(/^<h3>…/)` frágil; `aria-labelledby` colgando sin glosario | low | patch (hecho) | `card(x, false)`; el atributo se pone solo al rellenar |
| 6 | Ciego | Dos «por ejemplo» seguidos en la ficha Potencial | low | patch (hecho) | Un solo paréntesis con tres casos |
| 7 | Brechas | Ids de `HOW_OPEN` sin comprobar contra `Termino` | low | patch (hecho) | Prueba nueva |
| 8 | Ciego | Enlace roto en el README por renombrar «Reach paths» | false | rechazado | Verificado: ningún enlace apunta a `#reach-paths` |
| 9 | Ciego | Anclas `term-…` sin enlaces; el contrato describe «¿qué es esto?» | medium | diferido | La spec no lo pedía; historia aparte (36) |
| 10 | Ciego | El tono se fija al generar y no se cambia con el selector | low | rechazado | Diseño acordado: el tono lo elige la persona al generar |
| 11 | Ciego | Ficha 12 sin uso en la terminal | low | rechazado | La spec la pide para el HTML; `--detalle` la lista si aparece |
| 12 | Ciego y casos límite | Las fichas 1 y 2 más largas llegan a `--detalle` de la terminal | low | rechazado | Ajusta al ancho (Historia 30) y la suite pasa; es el mismo catálogo |
| 13 | Ciego | Español mezcla camino, caminos y recorrido | low | rechazado | Camino = la cadena; Recorrido = la vista; decisión de Alex |
| 14 | Ciego | Sin `@media print` de respaldo | low | rechazado | Los eventos `beforeprint` cubren Chrome y Edge; Safari móvil no es objetivo |
| 15 | Ciego | `<h2>` dentro de `<summary>`, términos plegados sin encabezado | low | rechazado | Patrón nativo de `<details>`; sin daño demostrado |
| 16 | Ciego y casos límite | Datos vacíos o ids duplicados en `glossary` | low | rechazado | Los genera el propio producto desde el catálogo; el esquema los valida |
| 17 | Ciego | Comentario CSS `.howto` bajo `/* limits */` | low | rechazado | Cosmético |

## Design Notes

Los textos viajan en los datos y no en `T_` porque el tono (tú/usted) lo decide el usuario al generar el reporte y `T_` solo sabe de idioma. El patrón es el de `catalog` (`_i18n`): cada texto lleva `es` e `en`.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa

**Manual checks (if no CLI):**
- Alex abre el reporte HTML en el navegador y confirma que ve primero «Cómo leer este reporte» con los niveles y los caminos explicados, en español y en inglés.
