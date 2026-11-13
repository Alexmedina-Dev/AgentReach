# Epic 6 Context: Saber qué agentes hay y por qué algo no se determinó

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

El usuario ve qué agentes de IA hay configurados, qué analiza AgentReach y qué solo reconoce, y el archivo y la clave que impiden un nivel, todo explicado en lenguaje llano. Las historias 24 a 26 están terminadas; esta épica queda abierta por la Historia 32 (explicar cada término técnico).

## Stories

- Story 6.1: Reconocer los agentes configurados con el catálogo
- Story 6.2: Por qué un nivel es «no determinado»
- Story 6.3: GitHub Copilot, un solo agente cuando la señal es compartida
- Story 6.4 (Historia 32): El reporte explica cada término técnico en lenguaje llano (pendiente)

## Requirements & Constraints

- Cada término técnico que aparece trae su «qué es» y su «qué significa para ti», sin jerga interna, desde un único catálogo fijo; nunca de un modelo de lenguaje.
- Bilingüe español/inglés; tono «tú» por defecto y «usted» con `--tono formal`; el inglés no cambia con el tono.
- El producto nunca dice «seguro» ni «sin riesgo»; «potencial» nunca se presenta como riesgo menor.
- Nunca valores de secretos en ninguna explicación ni mensaje.
- El resumen de la terminal sigue corto: resumen por nivel y los 3 hallazgos más urgentes; el listado y la explicación completa salen con `--detalle` y en el reporte HTML.
- Ningún identificador técnico (`hooks.PreToolUse`, `funcion_no_modelada`, `TH-n`) en el resumen sin su explicación al lado.

## Technical Decisions

- Hoy el catálogo de textos está indexado por tipo de hallazgo y por motivo de «no se pudo revisar»; falta un catálogo por concepto (11 términos).
- La autocomprobación conoce el hallazgo corregido (ubicación y tipo) pero el reporte solo recibe las razones y un contador; hay que conservar tipo, ubicación y el nivel antes y después.
- Los textos y las reglas de redacción viven en el contrato de UX `ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md` (secciones «Glosario y explicaciones» y «Cuándo y dónde aparece cada explicación»); es la fuente de los textos.

## UX & Interaction Patterns

- Terminal: una frase por término y solo donde la jerga aparece; explicación completa con `--detalle`.
- Todo texto impreso respeta el ancho de la terminal y no parte palabras.

## Cross-Story Dependencies

- Story 6.4 depende de 4.1 (reporte), 4.5 (HTML, para las historias 33 y 34 que la completan) y 6.2 (por qué no determinado).
- La parte del HTML (Historia 33) y la del README (Historia 34) se construyen después y reutilizan el catálogo que crea esta historia.
