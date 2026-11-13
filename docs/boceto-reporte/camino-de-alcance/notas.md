# Camino de alcance: notas (boceto, 2026-11-09)

Archivo: `camino-de-alcance.html` (un solo archivo, SVG/CSS/JS puros, sin red, sin guardar nada). Datos: `externo/datos-ejemplo.json` (ficticios), incrustados en el HTML.

## La idea en 3 frases
El alcance de un agente no es un punto sino una cadena: Agente, regla o permiso, Lugar (archivo y línea), Qué es, y Efecto posible. Cada hallazgo se dibuja como un camino de izquierda a derecha; los tramos que AgentReach sí comprobó van con línea continua y el último ("podría dar acceso a", no comprobado) va discontinuo y con la etiqueta "not checked / no comprobado". Al elegir un camino o una caja se ilumina toda la cadena, se atenúa el resto y un panel de cristal muestra los 8 campos.

## Cómo se arma el grafo
- Una columna por tipo de caja; cada hallazgo aporta 4 claves: agente = `platform_agent`; lugar = `location` + línea; qué es = `what` (texto EN); efecto = `whose` (texto EN).
- Regla de unión: dos hallazgos comparten caja si tienen la misma clave en esa columna. Las cajas compartidas se colocan en el promedio de las filas de sus caminos, y las flechas convergen o se abren desde ellas.
- Con los datos de ejemplo se unen: los 3 agentes (A reúne 4 caminos, B 3, C 2) y "Credencial en un archivo" (f1 y f2). Los lugares y los efectos son todos distintos, así que no se unen. Es la estructura real de los datos, no un adorno: con datos reales (varios hallazgos hacia el mismo servicio) habría más convergencia.
- Las flechas son por hallazgo (3 tramos cada uno) y llevan el icono y la forma del nivel de ese hallazgo. Una caja compartida muestra los iconos de todos los niveles que pasan por ella y el borde del más cierto.
- Filas ordenadas por agente, luego nivel (Comprobado, Potencial, Hipótesis), así no hay cruces de líneas con estos datos. Los filtros recalculan el grafo.
- Etiqueta del tramo 1 = `agent_rules` del hallazgo; tramo 2 = "contiene"; tramo 3 = "podría dar acceso a / no comprobado".

## Verificación hecha (Edge, Playwright, headless)
- Capturas: escritorio y móvil, oscuro y claro, una con camino seleccionado (f5), una con caja compartida seleccionada, ES, filtrada y vista de lista.
- Contraste medido sobre píxeles reales del cristal (texto oculto, muestreo del fondo tras cada texto, percentil 1, 4.5:1): 0 fallos en 6 configuraciones; mínimo 4.76 (oscuro) y 4.88 (claro).
- 0 errores o avisos de consola, 0 peticiones de red, sin desbordamiento horizontal a 1440, 390 y 360 px.
- Teclado: Tab llega al grafo (una sola parada), flechas arriba/abajo cambian de camino, izquierda/derecha avanzan por la cadena, Enter selecciona, Esc quita. `prefers-reduced-motion` quita el flujo de luz.
- Se corrigió: un botón "Detalles" que quedaba aplastado por títulos largos en móvil (texto fuera del botón, contraste 1:1).

## Lo que NO verifiqué
- Lector de pantalla real (NVDA/JAWS/VoiceOver): solo razoné la estructura (botones con etiqueta, vista de lista como alternativa, roving tabindex). La lista y el grafo son vistas alternas, no se leen las dos a la vez.
- Safari y Firefox; solo Edge. El respaldo sin `backdrop-filter` (@supports) y `prefers-contrast` están escritos pero no los probé forzando la falta de soporte.
- Contraste de iconos y bordes (3:1) solo a ojo; no medí texto en estado atenuado (las cajas atenuadas se leen menos a propósito; lo mismo está en el panel y la lista).
- Daltonismo con simulador; los niveles se distinguen por forma, borde e icono, no probado con simulador.
- Rendimiento con muchos hallazgos: el diseño es de columnas con filas de 100 px y no probé con 100+ caminos. No hay manejo de choques complejos entre cajas.
- Fuentes: pilas del sistema (Bahnschrift en Windows); en otros sistemas el título tendrá otro aspecto.
- Fuentes de glassmorphism: leí la página de FreeFrontend (parcial, 100 000 de 180 000 caracteres) y un resumen de búsqueda sobre accesibilidad (NN/g, Axess Lab y otras; no abrí cada una). No vi videos.

## Decisiones para Alex
1. ¿La línea continua también para Potencial e Hipótesis? Hoy sí (se vieron en archivos) pero el panel avisa "no del todo confirmados". Alternativa: línea más tenue o punteada en esos niveles.
2. ¿Las cajas de "Qué es" se unen solo por el mismo texto (hoy) o por familia (todas las "credenciales")? Por familia habría más convergencia, pero se pierde exactitud.
3. ¿Las cajas de efecto se unen por servicio real? El JSON de ejemplo solo trae un `whose` en texto libre; para unir "mismo servicio" hace falta un identificador estable.
4. Los límites ("No se pudo revisar") van como sección fija, no como cajas del grafo: ¿está bien?
5. Tema claro vistoso: ¿se queda como tema opcional o se alinea con la barra oscura de marca de `colores.md`?
6. Idioma y tema no se guardan (pedido: sin guardar datos). ¿Se acepta que vuelvan a EN y oscuro al recargar?
7. En pantallas menores de 1100 px se muestra la lista apilada en lugar del grafo; ¿se quiere un grafo con desplazamiento lateral en tabletas?
