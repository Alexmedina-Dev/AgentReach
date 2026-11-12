# Propuestas internas del reporte (2026-11-09)

Archivos: `propuesta-1-mapa-de-alcance.html` y `propuesta-2-expediente.html`. Cada uno es autocontenido (sin fuentes, scripts, imágenes ni CDN; sin red; no guarda nada). Interfaz en inglés con botones EN/ES, tema oscuro por defecto y claro llamativo (Paleta A). Datos: `externo/datos-ejemplo.json`, incrustado tal cual (100% ficticio). Se puede abrir con `?theme=light` o `?lang=es` solo para las capturas.

## Propuesta 1: Mapa de alcance

**Idea.** Un radar en SVG puro: el agente en el centro y cuatro anillos (R1 ligado a la tarea, R2 no determinado, R3 ajeno, R4 fuera de la carpeta). Cada hallazgo es un nodo con forma por nivel (octágono rojo Verified, triángulo ámbar Potential, rombo gris punteado Hypothesis), con su línea desde el centro y un barrido sutil. Al elegir un nodo se abre el detalle con los 8 campos, y la lista de tarjetas queda debajo, sincronizada (nodo a tarjeta y tarjeta a nodo, y los filtros atenúan los nodos).

**Qué la hace única.** Es la marca hecha reporte: los anillos y nodos son el logo. Los 6 puntos "could not check" viven en el borde exterior como violeta discontinuo y enlazan a la sección fija. La posición responde a "qué tan cerca de la tarea está", no solo a "qué tan grave es".

**Presentación.** "Esto es lo que su agente alcanza, de más cerca a más lejos de su tarea." Abrir el mapa, tocar el nodo rojo 1 y leer el detalle; luego mostrar que la lista y el idioma están a un clic.

## Propuesta 2: Expediente (dossier editorial)

**Idea.** Cada hallazgo es un caso (AR-001...) de un expediente. Un registro lateral (el índice de casos) y, a la derecha, la hoja abierta con sello rotado del nivel, tipografía serif editorial, cláusulas numeradas (§1 a §9) y la acción recomendada resaltada. El aviso "no se muestran valores" se vuelve una barra de censura donde iría el valor, y lo no revisado son "páginas faltantes" con borde rasgado.

**Qué la hace única.** Convierte la limitación de seguridad (nunca mostrar el secreto) en el motivo visual central: la barra negra. Se lee como un informe que uno puede imprimir y archivar, con sello, número de caso y anterior/siguiente.

**Presentación.** "Cada hallazgo es un caso cerrado y legible, no una alerta." Mostrarlo a quien revisa o audita, y abrir un caso con el sello y el valor censurado.

## Decisiones propias que Alex debe validar

- **Los anillos del mapa son una derivación mía.** El JSON no trae "distancia". Usé el campo "ajeno a la tarea" (no = R1, no determinado = R2, sí = R3) y puse el enlace que sale de la carpeta en R4. La posición angular es solo estética. Si el producto real tiene otra noción de distancia (dentro del proyecto, carpetas del usuario, entorno), hay que cambiar esa regla.
- La marca de "No se pudo revisar" en el mapa son 6 nodos que representan los 6 límites, no ubicaciones reales.
- Las nuevas fuentes: se usan pilas del sistema (Bahnschrift, Segoe UI Variable, Cascadia Code, Consolas, Iowan Old Style, Georgia). En Mac/Linux caerá a respaldos genéricos y se verá distinto.

## Qué verifiqué

Con Playwright y Microsoft Edge (headless): capturas de escritorio (1440) y móvil (390), oscuro y claro, de ambas, más una en español y dos de interacción (nodo + filtro; búsqueda + selección). Sin errores de consola ni peticiones de red, sin desbordamiento horizontal (scrollWidth = clientWidth). Se arregló en la marcha: desborde por el halo, etiquetas de anillo que chocaban con nodos y un salto de línea en un título.

## Qué NO verifiqué

- Contraste medido con herramienta: usé los hex de `colores.md` (ya medidos), pero no calculé de nuevo las combinaciones nuevas (p. ej. números de nodo sobre relleno tintado, texto gris en rombos, el título violeta grande).
- Lector de pantalla real (NVDA/Narrator), ni la navegación por teclado completa más allá de Tab y Enter sobre un nodo. Los nodos del SVG usan role="button" y tabindex; no es lo mismo que un `<button>`.
- Safari, Firefox, Edge/Chrome móvil reales; solo el motor de Edge de escritorio. `color-mix` no se usa, pero sí `overflow-x: clip`, `transform-box` y `clip-path`.
- Modo de alto contraste de Windows, daltonismo con simulador, impresión.
- Rendimiento con cientos de hallazgos: el mapa asigna posiciones a mano para los 9 de ejemplo; con más datos habría que calcular ángulos y evitar solapes.
- El mapa en móvil es legible pero pequeño (los nodos pasan a ~12 px); allí la lista es la vista principal.
- Reduced motion: lo desactivé en CSS pero no lo probé emulando la preferencia.
