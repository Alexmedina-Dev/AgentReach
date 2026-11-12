# Historia 20: diseño final en el generador HTML

**Estado: terminada (2026-11-10)**, con verificación manual pendiente de Alex (ver abajo).

## Qué cambió
- `reporting/plantilla_reporte.html` (copia idéntica en `docs/reporte-html/plantilla.html`) es ahora el diseño final (`docs/boceto-reporte/reporte-final`) leyendo los datos reales del esquema v1; se quitó todo lo ficticio (generador, tamaños de demo, agentes de ejemplo, sugerencias y reglas copiables, que no tienen datos).
- **Más de 60 hallazgos del agente elegido:** el diagrama general es un resumen estático sin nodos seleccionables: carpetas con hallazgos EN ORDEN ALFABÉTICO (AgentReach no registra el orden real de visita; el rótulo lo dice) y hallazgos por nivel con forma y palabra. El detalle va en Lista (vista por defecto), Tabla o Imprimir. Con 60 o menos, el grafo interactivo sigue.
- **Agentes configurados:** nuevo campo opcional `configured_agents` (esquema v1, aditivo). Los adaptadores aportan `evidencia` (archivos que EXISTEN: settings de proyecto/usuario/gestionada, `CLAUDE.md`, `.mcp.json`, `opencode.json(c)`, `.opencode/`; solo `lexists`, sin abrir). La plantilla dice «configurado», nunca «ejecutado», con la nota fija de que AgentReach no sabe si el agente corrió.
- **Imprimir:** no hay selector; se imprime lo que se ve (sin controles ni adornos).
- Cabecera con la distribución de la propuesta externa.

## Verificado
Playwright/Edge sin interfaz con 0, 5, 61, 300 hallazgos y el proyecto de prueba: 0 errores de consola, 0 peticiones externas, 0 desborde horizontal a 1440 y 390, 0 elementos interactivos en el diagrama con 61 y 300, EN/ES y tema, CSS de impresión emulado. Pruebas: `tests/test_reporte_html.py` (27). Capturas en `docs/boceto-reporte/reporte-final/capturas-h20/`.

## No verificado / diferido
- Impresión real desde el diálogo del navegador (y el grafo de ≤60 al imprimir: escala a 680 px en `beforeprint`).
- Contraste de texto (el diseño final ya tenía fallos medidos sin corregir), lector de pantalla, Safari, Firefox, teléfono real, exportar JSON/CSV en el navegador.
- «Imprimir» con miles de hallazgos pinta todo el detalle y puede ir lento.
- Comparación línea a línea de la cabecera con `propuesta-externa/index.html`.
- Sin revisión independiente con subagente de esta historia.
