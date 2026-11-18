# Epic 6 Context: Saber qué agentes hay y por qué algo no se determinó

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

El usuario ve qué agentes de IA están configurados en su proyecto o equipo, cuáles analiza AgentReach y cuáles solo reconoce, y qué archivo y clave impiden fijar un nivel («no determinado»), todo explicado en lenguaje llano y sin mostrar valores. Importa porque evita una falsa cobertura (ver un agente listado no significa que se haya revisado su alcance) y porque un novato debe poder entender el reporte sin salir de él.

## Stories

- Story 6.1: Reconocer los agentes configurados con el catálogo
- Story 6.2: Por qué un nivel es «no determinado»
- Story 6.3: GitHub Copilot, un solo agente cuando la señal es compartida
- Story 6.4: El reporte explica cada término técnico en lenguaje llano
- Story 6.5: «Cómo leer este reporte» va primero y siempre visible en el HTML
- Story 6.6: El README define los mismos términos que el catálogo
- Story 6.7: El resto de los textos del HTML siguen el tono elegido
- Story 6.8: Enlace «¿qué es esto?» junto a cada término
- Story 6.9: La caja de «efecto posible» no queda vacía
- Story 6.10: Un agente que no está en la carpeta ni en el equipo no aparece
- Story 6.11: «Cómo leer este reporte», en corto

## Requirements & Constraints

- Reconocer no es analizar: el catálogo (22 entradas) solo mira existencia de archivos y nombres de variables de entorno, nunca contenido ni valores, y dice «configurado», nunca «ejecutado». Solo Claude Code y opencode tienen adaptador y se analizan; los demás llevan el aviso «aún no analiza qué puede alcanzar» y no entran al selector ni mezclan niveles.
- Los nombres compartidos (`AGENTS.md`, `.mcp.json`, `.vscode/`, `.github/`, `.env`…) no identifican a un agente; salen como «No determinado» con la lista de candidatos. Copilot es un solo agente cuando la señal es compartida. Si hay varios agentes se reportan todos, sin elegir uno «principal».
- «No determinado» debe decir archivo y clave (de una lista fija), nunca valores, en terminal, HTML y exportaciones.
- Regla de visibilidad (Historia 40, decidida 2026-11-12): un agente con adaptador solo aparece (pestaña y hallazgos) si se detecta configurado en proyecto o equipo; si no se detecta ninguno, se muestran los dos con «analizado sin señales de configuración»; con `--agente` se muestra el pedido aunque no se detecte; el código de salida cuenta solo los agentes mostrados; ningún nivel cambia (los 67 casos del oráculo no varían).
- Texto: todo término se explica sin buscar fuera, en español (tú/usted) e inglés, sin emojis, nunca «seguro» ni «sin riesgo», sin identificadores técnicos (`hooks.PreToolUse`, `funcion_no_modelada`, TH-n) sin su explicación al lado. Deuda: el nombre de Copilot no es bilingüe.
- La caja «efecto posible» nunca queda vacía (TH-10 y TH-14 con proveedor `no_aplica` usan frase fija); TH-14 nunca muestra el comando del hook.

## Technical Decisions

- Un solo catálogo fijo de 12 fichas de términos (`core/catalogo_terminos.py`) alimenta terminal, HTML y README; sin modelo de lenguaje; cada ficha trae línea corta (`line`) y detalle (`what_is`, `means`, `to_do`) por tono e idioma. Ninguna salida redefine un término.
- El HTML es un solo archivo estático: el glosario viaja en los datos JSON incrustados (`{en, es}` con el tono elegido) y la plantilla no inventa textos; los identificadores `term-<id>` se conservan. Esquema en `docs/reporte-html/`.
- Todo pasa por la compuerta (`reporting/gate.py`): `texto.py` y `html.py` solo ven vistas, nunca un `Finding`. La autocomprobación debe decir cuál hallazgo (tipo y ruta) bajó de nivel.
- Registro de adaptadores: tupla fija en `app/auditar.py` (sin entry points); reconocimiento en `app/agentes.py`; la copia empaquetada del catálogo de agentes (`src/agentreach/data/`) debe ser idéntica byte a byte a la de `docs/agentes-catalogo/`.
- Pruebas: una por historia en `tests/`; deben comparar catálogo con README, comprobar ausencia de «seguro»/«sin riesgo» y cubrir el proyecto proyecto real local (solo Claude Code) y el del oráculo (ambos agentes).
- Convenciones: módulos y funciones en español sin tildes; dataclasses congeladas; todo texto de la terminal pasa por el único punto de ajuste de ancho.

## UX & Interaction Patterns

- HTML: «Cómo leer este reporte» es lo primero tras la cabecera, un `<details>` abierto por defecto y plegable, que se imprime abierto. Vista corta por defecto: frase de introducción más la frase corta de los tres niveles y del camino de alcance (80 palabras como máximo); el detalle va tras «Ver más» y los otros términos (hook, sandbox, no determinado…) en «Otros términos» plegados.
- Enlace «¿qué es esto?» junto a cada término: salta a su ficha y la abre; con foco visible, `aria-label` con el término, orden de tabulación igual al de lectura y anclas que funcionan sin JavaScript.
- El tono elegido (tú/usted) rige todo texto propio del HTML; `<html lang>` y `<title>` siguen el idioma elegido.
- Terminal: una frase (≤90 caracteres) por término, solo donde la jerga aparece; la explicación completa va en `--detalle` y en el HTML. Camino de alcance (Agente → Dónde → Qué hay → Efecto posible): línea continua = comprobado, discontinua = no comprobado; en inglés «Reach route» y la vista «Route map».

## Cross-Story Dependencies

- 6.5 depende de 6.4 (catálogo de términos) y de 4.5; 6.6, 6.7, 6.8, 6.9 y 6.11 dependen de 6.5; 6.6 también de 6.4.
- 6.10 depende de 6.1 (detección de agentes configurados) y toca la lista de agentes de `app/auditar.py` y el cálculo del código de salida.
- 6.8 reutiliza los `term-<id>` que 6.11 conserva, y abrirá el detalle plegado de 6.11.
- 6.3 dejó deuda del nombre bilingüe de Copilot, que se resuelve en la Story 7.2 (épica 7).
