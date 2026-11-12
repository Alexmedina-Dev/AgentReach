# Notas para Alex: pedir diseños a un chat externo

## Cómo usarlo
1. Abra `brief-diseno.md` y copie TODO su contenido en el chat externo.
2. Adjunte (o pegue) `datos-ejemplo.json`. Es 100% ficticio.
3. Pida los 3 diseños (el brief ya lo pide). Si responde con uno solo, insista en que son 3 distintos.
4. Pida correcciones por separado, una propuesta a la vez, citando el criterio que falla (sección 8 del brief).

## Qué NO pegar nunca
- Reportes reales de su equipo o de su máquina.
- Rutas reales (carpetas, nombres de usuario, nombres de equipos o de repositorios).
- Credenciales, tokens, claves o cualquier valor secreto, aunque sea "de prueba".
- El proyecto de prueba de AgentReach ni sus respuestas esperadas.
- Su memoria local de Claude ni archivos de configuración de agentes.
- Nombres de cuentas de GitHub.

Si necesita más datos de ejemplo, invente más hallazgos ficticios; no copie los reales.

## Cómo traer los diseños de vuelta
1. Guarde cada HTML en `docs/boceto-reporte/externo/propuestas/` (por ejemplo `propuesta-1-tarjetas.html`).
2. **No abra ese HTML en el navegador todavía.** Pídame que lo revise primero: un HTML externo puede traer scripts, llamadas a internet o código que no se ve a simple vista.
3. Yo reviso: que no cargue nada externo, que no use red ni almacenamiento, que no tenga scripts ocultos, y que los datos sean solo los del JSON.
4. Cuando yo lo apruebe, lo abre.

## Lista de comprobación para evaluar cada propuesta
- [ ] Los 8 campos salen, en el orden fijo, en cada hallazgo.
- [ ] Hay resumen por nivel arriba.
- [ ] Sale la sección fija "Qué no pudo revisar AgentReach" (partes: esta carpeta y límites de la herramienta).
- [ ] Sale el aviso "No se muestran valores de secretos".
- [ ] Los niveles se distinguen sin color (icono, forma y palabra).
- [ ] Rojo solo en "Comprobado"; violeta en "No se pudo revisar"; menta en lo correcto y acciones; azul en información.
- [ ] Colores de marca exactos (`#0B1114`, `#121C20`, `#3DF5D0`, `#FFB224`, `#EAF4F2`, `#A9BDB9`, `#7C928E`).
- [ ] Contraste de texto de 4.5:1 o más en tema oscuro y claro.
- [ ] Tema oscuro por defecto; tema claro llamativo; respeta `prefers-color-scheme` y `prefers-reduced-motion`.
- [ ] Botones EN y ES funcionan y cambian todo el texto.
- [ ] Filtros y búsqueda funcionan.
- [ ] Se usa con teclado (foco visible) y se ve bien en el móvil, sin scroll horizontal.
- [ ] Cero peticiones externas: sin fuentes, scripts, imágenes ni CDN; funciona sin internet.
- [ ] No guarda datos (sin localStorage ni cookies).
- [ ] No inventó funciones ni datos.
- [ ] Lenguaje llano, sin códigos sin explicar.
- [ ] Las 3 propuestas son de verdad distintas.
