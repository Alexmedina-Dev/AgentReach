# Reporte final de alcance: notas (2026-11-10)

Archivo: `reporte-final.html` (un solo archivo; HTML, CSS, JavaScript y SVG en línea; sin red; no guarda datos). Capturas en `capturas/`.

## 1. Qué tomé de cada diseño

**De la base (`camino-de-alcance-v2`):**
- Vistas Graph, Table, List y Print; selector de agente (cada agente con sus propios niveles, sin mezclar); botones de tamaño de demo (5, 20, 60, 300).
- Filtros de carpeta, tipo y texto; copiar ruta:línea; enlace permanente en la dirección (`#`); reglas de honestidad (línea continua = comprobado, discontinua = no comprobado); sección "Qué no pudo revisar".
- Generador de datos ficticios y mismo diseño de tarjetas y grafo.

**De la propuesta externa (`propuesta-externa`):**
- Encabezado: logo, radar, aurora de color y cristal. En tema oscuro, igual que la propuesta. En tema claro, usa la paleta general de la página; para que el logo se lea sobre fondo claro, va sobre un recuadro oscuro.
- Símbolo del logo y textos de niveles con forma, borde y palabra (no solo color).

## 2. Decisiones

- **Radar**: dibuja solo los niveles del agente elegido. Con más de 60 hallazgos, los puntos se dibujan como círculos pequeños.
- **Vista por defecto**: sin enlace, 12 o menos hallazgos abren en Grafo (camino completo); más abren en Lista. Un enlace con `agent` o `size` abre en Lista, como pidió Alex. El botón de Tabla sigue disponible. Esto cambia la base: antes, con más de 60, abría en Tabla.
- **Lista**: cada tarjeta muestra el camino completo y el bloque "Qué hacer" visible, sin tener que abrir detalles.
- **"Qué hacer"**: usa el campo opcional `suggestion` (texto y, si aplica, una regla de denegar copiable). Si el dato no trae sugerencia, muestra el texto general de la base. Siempre dice que AgentReach no cambia archivos y que una regla de denegar es una política del agente, no una barrera del sistema. La regla usa una sintaxis ilustrativa que hay que ajustar al agente antes de usarla.
- **Tema**: al cambiar entre claro y oscuro se vuelve a pintar toda la página (antes solo se redibujaba el grafo). El papel de impresión sigue siendo blanco a propósito: la impresión es en blanco y negro.
- **Exportar** (JSON y CSV) ahora incluye la sugerencia y su regla. No lo probé en el navegador; solo cambié el código.

## 3. Verificado (Playwright con Microsoft Edge, headless)

- Capturas: 16 PNG en `capturas/` (escritorio 1440 y móvil 390; oscuro y claro; 5 y 300 hallazgos; vistas Lista y Grafo).
- Consola: 0 errores ni avisos. Peticiones de red: 16, todas locales; ninguna externa.
- Desbordes horizontales: ninguno en 1440 ni en 390.
- Copiar regla: aparece el aviso "Copied".
- Búsqueda "credential" con 300 hallazgos: 58 de 300 caminos (texto del contador).
- Cambiar a Tabla actualiza la dirección (`view=table`).
- Enlace permanente: abre el hallazgo indicado con sus detalles.
- Niveles por agente: el agente B no muestra Hipótesis (sus tarjetas son Comprobado y Potencial) y el agente C no muestra Comprobado (sus tarjetas son Potencial e Hipótesis). Verificado con recarga de página.
- Tema: cambia el fondo, los textos, los bordes y el radar. Excepción: una fila de detalle no se midió porque estaba plegada.

## 4. No verificado o pendiente

- **Contraste: no cumple con mi medición.** Medí cada texto con muestreo de píxeles (en vez de colores declarados): el 1% de píxeles más desfavorables. Hay textos de la lista por debajo de 4.5 (la norma de contraste normal): etiquetas de cadena ("Qué es", "Dónde", "Efecto posible", "Qué hacer") y la nota de honestidad de "Qué hacer", con mínimos de 1.04 a 1.1 en oscuro y claro. El mínimo de la vista Grafo en escritorio fue 2.59. Causa probable: líneas decorativas (bordes punteados violetas y menta) que caen dentro del rectángulo del texto. No lo confirmé. Antes de dar por bueno el contraste hay que revisar esas tarjetas a mano y corregir o confirmar el método.
- Lector de pantalla, Safari, Firefox y teléfono real: no probados.
- Impresión desde el diálogo del navegador: no probada.
- Exportar JSON y CSV en el navegador: no probado.
- Rendimiento con 300 hallazgos en la vista Lista: no medido.
