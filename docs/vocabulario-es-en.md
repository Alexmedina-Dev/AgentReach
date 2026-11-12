# Vocabulario ES / EN de AgentReach

Para qué sirve este documento: que el proyecto use **la misma palabra** siempre, en español y en inglés, y que el texto en inglés se traduzca bien con un traductor automático (como el del navegador).

Cómo leerlo: **ES** es la palabra en español, **EN** la palabra en inglés, y la última columna avisa de qué palabras se traducen mal y cómo evitarlo.

## 1. El lema

| ES | EN | Explicación simple | Nota de traducción |
|---|---|---|---|
| (ver variantes abajo) | **Know what your agents can reach.** | Descubre a qué cosas de tu computador puede llegar un agente de IA. | `reach` es la palabra más difícil: un traductor la puede convertir en "alcance" (que suena a tamaño), "alcanzar" (como estirar la mano) o "contactar". Por eso, en el cuerpo del README en inglés se usa `access` y solo se deja `reach` en el lema y en el nombre. |

### Variantes del lema en español

1. **"Sabe a qué puede llegar tu agente."** (o "Descubre a qué puede llegar tu agente de IA.")
2. **"Mira qué puede tocar tu agente."**
3. **"Conoce el alcance de tu agente."**

**Recomendación: la 1.** Motivos:

- "llegar a" se entiende como un camino ("llegar hasta tu carpeta de claves"), no como un tamaño. Es justo lo que hace la herramienta.
- Conserva la idea de `reach` y suena parecido al lema en inglés.
- La 2 es clara, pero "tocar" sugiere que el agente modifica cosas, y la herramienta también habla de leer.
- La 3 es la que Alex quiere evitar: "alcance" puede leerse como "tamaño".

## 2. Términos clave

| ES | EN | Explicación simple | Nota de traducción |
|---|---|---|---|
| a qué puede llegar / alcanzable | what it can reach / reachable | Lo que el agente puede leer o tocar desde donde trabaja, aunque nadie se lo haya pedido. | En español evitar "alcance" solo; preferir "a qué puede llegar". En inglés, en el cuerpo usar `can access` y `is accessible`; `reachable` solo con una explicación al lado. |
| alcance (con cuidado) | (evitar `scope`) | Si se usa, aclarar que significa "hasta dónde puede llegar", no tamaño. | `scope` traduce a "alcance", "ámbito" o "mira" según el caso. Usar `limit`, `permissions` o `what the agent can access`. |
| hallazgo | finding | Cada elemento que AgentReach encuentra y muestra en el reporte, con evidencia y nivel de confianza. | `finding` puede salir como "encontrar" (verbo) o "conclusión". Definirlo la primera vez ("each item in the report, called a finding") y usarlo siempre igual. |
| evidencia | evidence | Los hechos que sostienen el hallazgo: ruta, permiso, regla. | Sin problema. |
| nivel de confianza | confidence level | Qué tan seguro está AgentReach de cada hallazgo. | Sin problema. |
| comprobado | verified | Se confirmó que el archivo existe, que el sistema permite leerlo y que ninguna regla del agente lo bloquea. | `verified` se traduce bien como "verificado/comprobado". Evitar `confirmed` y `proven` para no mezclar palabras. |
| potencial | potential | Podría alcanzarse, pero falta confirmar algo. | `potential` puede salir como "posible" o "potencial"; ambos sirven. |
| hipótesis | hypothesis | Indicio débil que conviene revisar a mano. | Sin problema. |
| adaptador | adapter | Pieza que entiende la configuración de un agente concreto (Claude Code, opencode). | Sin problema. Evitar `plugin` en este sentido. |
| núcleo (independiente de cualquier agente) | core (works with any agent) | La parte central de AgentReach, que no depende de ningún agente. | No usar `agnostic`: se traduce como "agnóstico" y suena a religión. |
| solo lectura | read-only | AgentReach mira, nunca cambia nada. | Sin problema. |
| agente de IA | AI agent | Programa con inteligencia artificial que puede leer archivos y ejecutar comandos por ti. | `agent` a veces sale como "agente" de ventas o de policía; el contexto de IA ayuda. |
| plataforma | platform (the program that runs the agent) | El programa que ejecuta al agente (Claude Code, opencode). | Definirla en una frase la primera vez. |
| sandbox | sandbox | Caja aislada que limita lo que un programa puede tocar. | Los traductores a veces la dejan como "sandbox" o la traducen como "caja de arena". Escribirlo así: `sandbox (an isolated box that limits what a program can access)`. |
| superficie (de ataque) | (evitar `surface`) | Conjunto de puntos por donde algo podría entrar. | `surface` traduce literal ("superficie") y no se entiende. No se usa en el README. |
| sin valores de secretos | no secret values | El reporte nunca muestra una contraseña o token, solo dónde está. | Sin problema. |
| opt-in | opt-in (off by default, you turn it on) | Algo apagado hasta que tú lo enciendes. | Los traductores lo dejan igual. Explicarlo siempre en la misma frase. |
| núcleo + adaptadores | core + adapters | Estructura: una parte común y una pieza por cada plataforma. | Sin problema. |
| symlink / junction | symlink / junction | Accesos directos a nivel del sistema que llevan a otra carpeta. | Dejarlos en inglés y definirlos una vez. |
| token / credencial | token / credential | Clave o contraseña que da acceso a un servicio. | Sin problema. |
| permisos / ACL | permissions / ACL (access control list) | Lista de quién puede leer, escribir o ejecutar un archivo. | Escribir la sigla con su nombre completo la primera vez. |

## 3. Los 8 campos del hallazgo

Cada hallazgo del reporte responde estas ocho preguntas. Los textos de la tabla son los nombres propuestos para mostrar en el reporte.

| # | ES | EN | Explicación simple | Nota de traducción |
|---|---|---|---|---|
| 1 | ubicación | location | Dónde está (ruta de archivo, variable, etc.). | `location` es seguro. No usar `place` ni `path` como título. |
| 2 | qué es y de quién | what it is and whose it is | Qué clase de cosa es (token, clave) y a qué usuario o cuenta pertenece. | Mejor escribir `whose it is` que `owner`, porque `owner` puede salir como "dueño" legal. |
| 3 | nivel y por qué | level and why | El nivel de confianza (comprobado, potencial, hipótesis) y la razón. | Usar `confidence level` la primera vez y luego `level`. |
| 4 | ajeno a la tarea | unrelated to the task | Si esto no tiene que ver con lo que se le pidió al agente. | Evitar `out of scope` (scope) y `irrelevant` (suena a insulto). |
| 5 | plataforma y agente | platform and agent | Qué programa ejecuta al agente y qué agente es. | Sin problema. |
| 6 | postura del agente | agent rules (what the agent is told it may do) | Las reglas de permitir, preguntar o denegar que la plataforma declara para el agente. Son reglas escritas, no una barrera del sistema. | `posture` traduce como "postura corporal". Usar `agent rules` o `declared rules`. |
| 7 | qué hacer | what to do | Acción sugerida. AgentReach no la ejecuta. | Evitar `mitigation` (suena técnico) y `remediation`. |
| 8 | qué significa | what it means | Explicación sencilla de por qué importa. Es texto fijo por tipo de hallazgo. | Sin problema. |

En el ejemplo del README, el reporte usa las etiquetas en el orden: ubicación, qué es, valor (omitido), por qué, ajeno a la tarea, agente, postura, qué hacer, qué significa.

## 4. Reglas para escribir en inglés pensando en la traducción automática

1. Frases cortas (una idea por frase).
2. Sin modismos ni juegos de palabras. Evitar frases como `out of the box`, `under the hood`, `heads up`.
3. Sin verbos con preposición ambigua (`set up`, `look into`): usar `configure`, `check`.
4. Siempre la misma palabra para la misma idea (no alternar `finding`, `result`, `issue`).
5. Definir cada sigla la primera vez (`ACL`, `MCP`, `SSH`).
6. Evitar `can` ambiguo cuando se quiere decir permiso: usar `is allowed to` o `is able to` según el caso.
