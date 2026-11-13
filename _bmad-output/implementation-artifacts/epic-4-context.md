# Epic 4 Context: Entender el resultado de un vistazo

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

El usuario lee el reporte de AgentReach en la terminal y en el navegador, en español o inglés, con color accesible, un comando `doctor` y un flujo diario corto, en cualquier terminal. Las historias 13, 13b, 13c, 19, 20 y 21 están terminadas; esta épica queda abierta solo por una corrección nueva (colores legibles en cualquier fondo).

## Stories

- Story 4.1: Reporte con ocho campos, idiomas, orden, autocomprobación y código de salida
- Story 4.2: Reporte de terminal: ancho, color, codificación y limpieza
- Story 4.3: Marca, `doctor`, tema y tono
- Story 4.4: Reporte HTML estático
- Story 4.5: Diseño final del reporte HTML
- Story 4.6: Uso diario
- Story 4.7 (Historia 29): Colores legibles en cualquier terminal (pendiente)

## Requirements & Constraints

- El color nunca es la única señal: cada nivel lleva símbolo y palabra, con respaldo ASCII; sin color no sale ningún `ESC`.
- Sin emojis. Solo símbolos de texto.
- El banner de marca es identidad, no contenido: solo sale en una terminal interactiva, nunca con redirección, `NO_COLOR`, `--no-banner`, `--json`, `--salida`, `TERM=dumb` ni menos de 40 columnas.
- Paleta oficial de la marca en fondo oscuro: AGENT `#EAF4F2`, REACH `#3DF5D0`, texto secundario `#7C928E`; fondo de marca `#0B1114`. En fondo oscuro todo cumple contraste y no debe cambiar.
- Nada puede quedar ilegible aunque no se sepa si el fondo es claro u oscuro. Mínimo de contraste: 4,5 a 1 en texto, 3 a 1 en las letras grandes del logo.
- «AGENT» y «REACH» deben verse como una sola marca: combinar entre sí, no solo leerse.
- Producto bilingüe español/inglés y dos tonos (cercano y formal); el idioma y el tono de todo texto impreso cubren las cuatro combinaciones.
- Reglas no negociables que no se tocan: solo lectura, sin red, sin valores de secretos, sin ejecutar programas externos, solo biblioteca estándar.

## Technical Decisions

- Detección del tema por capas, de la más a la menos fiable: `--tema`, `AGENTREACH_TEMA`, `COLORFGBG`, consulta del color de fondo a la terminal (exploración opcional, límite de 200 ms, sin bloquear y sin leer de la entrada estándar si no hay terminal), y por último los colores del propio tema (primer plano por defecto y cian normal ANSI 36). Orca y Windows Terminal no definen `COLORFGBG`.
- Con fondo conocido, «REACH» conserva matiz y saturación de la marca y solo cambia la luminosidad hasta 3 a 1; si no llega, toma el de más contraste con luminosidad entre 20 % y 80 %. «AGENT» toma el color de marca de más contraste (`#EAF4F2` o `#0B1114`).
- La paleta vive en `reporting/formato.py` (`pintar`, tema claro/oscuro) y el banner en `reporting/marca.py` en tres tamaños con respaldo ASCII.
- El reporte se arma entero y se escribe de una vez; el color se aplica después de ajustar el ancho.

## UX & Interaction Patterns

- Flujo diario: banner mediano con una línea en blanco antes, pregunta de permiso `(S/N)`, resumen corto por nivel y los 3 hallazgos más urgentes, aviso de dónde quedó el reporte visual y pregunta de abrirlo.
- Referencia visual aprobada por Alex del logo adaptativo: `docs/presentacion-terminal/vista-previa/logo-temas.html`. La verificación final la hace Alex en Orca real (fondo claro).

## Cross-Story Dependencies

- Story 4.7 depende de Story 4.3 (banner, tema y `pintar`).
- La Historia 30 (ancho de los textos impresos) depende de 4.2 y de la Story 5.5 y vive en la Épica 5.
