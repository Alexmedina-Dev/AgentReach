# Historia 19: reporte HTML estático (`--formato html`)

**Estado: terminada (2026-11-10)**, salvo la verificación manual en navegador (criterio m), que queda para Alex.

## Qué hace
`agentreach audit RUTA --formato html --salida ARCHIVO.html` escribe UN archivo HTML con los mismos datos del reporte de texto, por agente (Claude Code, opencode, y «sin agente específico» solo si tiene hallazgos).
- Parte de `DatosReporte` (la compuerta `gate.py`): nunca ve un `Finding` ni un archivo del proyecto, así que no puede llevar valores de secretos ni rutas reales.
- Plantilla empaquetada `reporting/plantilla_reporte.html` (verificada dentro del wheel); el marcador de datos aparece una sola vez.
- Esquema 1 de `docs/reporte-html/esquema-datos.md`; se añadió `initial_language` (opcional) y el motivo `funcion_no_modelada`.
- Sin recursos externos, con `default-src 'none'`. JSON seguro: `<`, U+2028 y U+2029 escapados.
- `--formato html` exige `--salida` (si no, código 2); la salida dentro de la carpeta auditada se rechaza; pasarse de 20 000 hallazgos por agente o 20 MB da código 3 y no deja archivo parcial.

## Pruebas
`tests/test_reporte_html.py` (23): sin recursos externos, canarios ausentes, escape del bloque, rutas peligrosas escritas y recortadas, validación contra el esquema JSON, por agente sin duplicados, cobertura del catálogo en EN/ES, límites siempre presentes, cero hallazgos, determinismo, 5000+5000 filas en menos de 5 s, topes, árbol idéntico y ningún programa lanzado.

## Pendiente / diferido
- (m) revisión visual en navegador real (Playwright): de Alex.
- La nota de esquema opencode (`DatosReporte.esquemas`) sale en el texto, no en el HTML (la plantilla no tiene dónde ponerla): diferido.
- Revisión independiente con subagente de la 19: no se hizo aparte; la compuerta ya estaba revisada en la 13.
