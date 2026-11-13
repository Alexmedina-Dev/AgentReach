---
name: AgentReach
status: final
version: "0.1"
created: 2026-11-11
updated: 2026-11-11
sources:
  - _bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md
  - _bmad-output/planning-artifacts/epics.md
  - docs/reporte-terminal/diseno.md
  - docs/presentacion-terminal/diseno.md
  - README.md
---

# AgentReach: Experience Spine (la experiencia de EXPLICAR, Historia 32)

> Primer contrato formal de UX de AgentReach. Se enfoca en cómo el producto explica sus propios términos (FR-11, UX-DR15). Emparejado con `DESIGN.md`, que manda en lo visual. Las decisiones salen de `.memlog.md`; lo inferido está marcado [ASSUMPTION] y reunido al final.

## Foundation

Dos superficies: la **terminal** (Windows incluida; interactiva, con preguntas S/N) y el **reporte HTML** estático. Más un README único en inglés. Todo lo que se explica sale de **un solo catálogo fijo** (sin modelo de lenguaje: el mismo hallazgo produce siempre el mismo texto), nunca contiene valores de secretos y existe en español (tú o usted) e inglés. La terminal es corta y manda; el HTML es la versión extendida. Idea rectora: **cada palabra técnica que el reporte usa se puede entender sin salir del reporte** (FR-11: «un novato puede entender el hallazgo sin buscar términos fuera del reporte»), y el reporte jamás promete seguridad.

## Information Architecture

| Qué | Terminal | HTML |
|---|---|---|
| Resumen por nivel + 3 más urgentes | Primero, corto (Historia 22) | `#summary` |
| Explicación de un término | Una frase, solo donde la jerga aparece | `<details>` «Cómo leer este reporte» (fichas completas) y enlace «¿qué es esto?» junto a cada término |
| Explicación completa y listado | `--detalle` | Vistas Recorrido, Tabla, Lista y panel lateral |
| Agentes configurados | Sección propia, con su frase | `#cfg` |
| Por qué hay «no determinado» | Sección propia (FR-32), solo si hay | Aviso + fichas |
| Qué no se pudo revisar y límites | Cierre corto; completo en `--detalle` | `#limits`, siempre visible |
| Autocomprobación | Aviso que dice cuál hallazgo y a qué nivel pasó | Nota en el hallazgo afectado |
| Glosario en inglés | No | README (mismos términos y sentido) |

Orden de la terminal: banner, encabezado, RESUMEN, AGENTES CONFIGURADOS, POR QUÉ HAY NIVELES «NO DETERMINADO», LO MÁS URGENTE, alcance, cierre. Orden del HTML: barra, **«Cómo leer este reporte»** (primero, abierto), aviso, `#cfg`, `#summary`, vistas, `#limits`.

## Voice and Tone

Lenguaje llano, frases cortas, voz activa, una idea por frase. Siglas definidas la primera vez (SSH, MCP, ACL, token). Tres variantes, todas del mismo catálogo: español cercano (**tú**, por defecto), español formal (**usted**, con `--tono formal`) e inglés neutral. Todo texto del HTML, incluidos los de la plantilla, sigue el tono elegido.

| Di | No digas |
|---|---|
| «No es una alarma ni una garantía: es un punto ciego» | «No significa que sea inseguro» / «es seguro» / «sin riesgo» |
| «Potencial: probable, falta confirmar algo» | «Potencial: riesgo menor» |
| «AgentReach no sabe qué decide ese programa» | «Función que AgentReach no modela» |
| «No se pudo confirmar dónde está» | «La línea citada no se pudo confirmar» |
| «Un hallazgo bajó a potencial porque…» | «Regla de nivel violada» |
| «Configuración (versión 2)» solo si importa | «Esquema de configuración 2.x» |

Reglas duras: sin emojis; **nunca «seguro» ni «sin riesgo»** (lo no revisado no es seguro); «potencial» nunca se presenta como menor; jamás un valor de secreto, solo tipo, archivo y clave; los identificadores técnicos (`hooks.PreToolUse`, `funcion_no_modelada`, TH-n) nunca aparecen sin su explicación al lado.

## Component Patterns

Visual en `DESIGN.md`. Aquí, el comportamiento.

| Componente | Uso | Reglas |
|---|---|---|
| Línea de término (terminal) | Donde aparece la jerga | Una sola frase, ≤90 caracteres, ajustada al ancho. Solo si el término está en pantalla (no se imprime el glosario entero). |
| Bloque de explicación | `--detalle`, HTML | «Qué es», «Qué significa para ti», «Qué puedes hacer», en ese orden, mismo texto de la ficha. |
| Enlace «¿qué es esto?» (HTML) | Junto a cada término | Salta a la ficha dentro de «Cómo leer este reporte» y la abre; Escape o el enlace «volver» regresan al punto de origen. |
| «Cómo leer este reporte» | HTML | `<details>` abierto por defecto (se puede plegar), primer bloque tras la cabecera; los niveles y el camino de alcance a la vista y los demás términos plegados; contiene fichas, un ejemplo por nivel y por agente. |
| LO MÁS URGENTE | Terminal | Tres hallazgos: chip, agente, título, ruta y **una línea «→ qué hacer»** [ASSUMPTION]. |
| Aviso de autocomprobación | Terminal, HTML | Dice cuál hallazgo (tipo y ruta, sin valores) y a qué nivel pasó. Requiere ampliar el dato (ver Dependencias técnicas). |
| Causa de «no determinado» | Terminal, HTML | Archivo y clave en lenguaje llano, no la clave cruda sola; la clave técnica va entre paréntesis después de la frase. |

## State Patterns

| Estado | Tratamiento |
|---|---|
| Con hallazgos | Resumen por nivel (solo niveles con conteo > 0), 3 más urgentes, frase de término solo para los niveles y términos presentes. |
| Sin hallazgos | `√ SIN HALLAZGOS` + «Esto cubre solo lo que AgentReach pudo revisar; no significa que lo demás esté bien.» + enlace a límites. Nunca «todo bien». |
| Muchos «no determinado» | Una sola explicación de hook/función y la lista de causas (archivo y clave), no una explicación por hallazgo; el resto referencia («igual que arriba»). |
| Terminal sin color (`NO_COLOR`, redirección) | Símbolo + palabra bastan; sin banner. |
| ASCII (`--ascii`, `AGENTREACH_ASCII=1`, sin Unicode) | `[!!] [!] [?] [-]`, `->`, banner ASCII, sin tildes en el respaldo. |
| Ancho angosto (<60) | Se usa 60 como ancho de trabajo; bajo 40, banner mínimo ASCII; las rutas van enteras aunque excedan. |
| Fondo claro / oscuro / desconocido | Ver «Terminales y anchos». Nunca se pinta el fondo. |
| Autocomprobación bajó algo | Aviso con cuál y a qué nivel; el hallazgo se muestra en su nivel corregido, nunca en el original. |
| HTML sin JavaScript de ayuda | El `<details>` funciona nativamente; los enlaces «¿qué es esto?» son anclas normales. |

## Interaction Primitives

- **Permiso S/N:** dos niveles; la mayúscula marca el predeterminado, «(S/N)» no se separa. Responder N deja lo que depende de las reglas en potencial y la explicación lo dice.
- **`--detalle`:** listado completo, con códigos, motivos y explicaciones largas. El cierre de la terminal lo nombra y dice qué es: «el listado completo, con la explicación de cada hallazgo».
- **`--tono cercano|formal`:** cambia tú/usted en terminal y HTML. El inglés no cambia.
- **`--tema claro|oscuro|auto`** [ASSUMPTION sobre los valores]: elige la variante de color; `auto` no pinta fondo.
- **`--ascii`:** respaldo sin Unicode ni color de adorno.
- **Abrir el reporte:** la terminal dice la ruta del HTML guardado, ajustada al ancho; abrirlo es acción de la persona [ASSUMPTION: no lo abre sola].
- **HTML:** el `<summary>` de «Cómo leer este reporte» se activa con Enter o Espacio; Tab recorre enlaces «¿qué es esto?» en el orden de lectura; Escape cierra el panel lateral.

## Accessibility Floor

- Contraste: texto ≥4,5:1 y logo ≥3:1 (con fondo conocido); la variante sin fondo conocido usa `{colors.brand-mint-neutral}` (≥4,5:1 sobre blanco y negro) y `{colors.brand-muted}` para versión y lema.
- El color nunca es la única señal: símbolo + palabra siempre (`{components.level-chip-verified}` y hermanos); en HTML, además, forma de borde.
- Terminal pensada para lectores de pantalla: sin emojis, sin dibujos que el lector deletree (el banner se omite o queda una línea de texto), tablas reducidas a líneas.
- HTML: `<details>` nativo, enlaces con texto propio («¿qué es “potencial”?», no solo «¿qué es esto?» para el lector de pantalla: `aria-label` con el término), foco visible ≥3:1, orden de tabulación igual al de lectura, `lang` correcto por idioma, tamaño de texto ampliable sin pérdida.
- Impresión: la vista Imprimir incluye las fichas de los términos presentes y respeta el tono elegido; los `<details>` salen abiertos [ASSUMPTION].
- Sin parpadeo ni animación necesaria.

## Terminales y anchos

- Ancho de trabajo = columnas reales, entre 60 y 100 para el reporte. Todo texto impreso (bienvenida, preguntas, avisos, «reporte guardado») se ajusta por un único punto y no parte palabras; una ruta sin espacios va entera; «(S/N)» no se separa (Historia 30).
- Fondo claro conocido: REACH con luminosidad movida hasta ≥3:1 y AGENT en `{colors.brand-bg}`; fondo oscuro conocido: AGENT en `{colors.brand-ink}`; desconocido (hoy): AGENT en el texto normal, REACH `{colors.brand-mint-neutral}`, 16 colores en cian normal (36). La detección real del fondo es la Historia 31.
- Los niveles usan la columna «claro» u «oscuro» de `DESIGN.md`; con fondo desconocido, la variante de mayor contraste en ambos.
- Cada explicación de una línea cabe en 90 caracteres; con menos de 90 columnas se ajusta a dos líneas, nunca se trunca.

## Glosario y explicaciones

Conjunto fijo de 12 términos (el 12, «camino de alcance», se añadió en la Historia 33). Cada ficha trae, completas, las tres variantes (tú, usted, EN) de **(i)** la línea de terminal (una frase, ≤90 caracteres) y **(ii)** la explicación larga del HTML («Qué es», «Qué significa», «Qué puedes hacer»). Ningún texto remite a otra variante: el catálogo los guarda por separado. Sin jerga interna, sin valores. Mismo sentido que el glosario del README.

### 1. Nivel comprobado
- **Terminal.** Tú: «Comprobado: el agente puede llegar a esto hoy. Atiéndelo primero.» · Usted: «Comprobado: el agente puede llegar a esto hoy. Atiéndalo primero.» · EN: «Verified: the agent can reach this today. Deal with it first.»
- **HTML (tú).** *Qué es:* AgentReach confirmó tres cosas a la vez: el archivo o dato existe, el sistema operativo deja leerlo a quien ejecuta el agente y ninguna regla del agente lo impide. El permiso se calcula con los datos que guarda el sistema sobre quién puede leer el archivo, sin abrirlo para probarlo. *Qué significa para ti:* hoy mismo el agente puede leerlo. No es una sospecha, aunque tampoco quiere decir que ya lo haya leído. *Qué puedes hacer:* atiéndelo primero; cada hallazgo trae su paso concreto.
- **HTML (usted).** *Qué es:* AgentReach confirmó tres cosas a la vez: el archivo o dato existe, el sistema operativo deja leerlo a quien ejecuta el agente y ninguna regla del agente lo impide. El permiso se calcula con los datos que guarda el sistema sobre quién puede leer el archivo, sin abrirlo para probarlo. *Qué significa para usted:* hoy mismo el agente puede leerlo. No es una sospecha, aunque tampoco quiere decir que ya lo haya leído. *Qué puede hacer:* atiéndalo primero; cada hallazgo trae su paso concreto.
- **HTML (EN).** *What it is:* AgentReach confirmed three things at once: the file or data exists, the operating system lets whoever runs the agent read it, and no agent rule blocks it. The permission is worked out from the data the system keeps about who can read the file, without opening it to test it. *What it means for you:* the agent can read it today. It is not a suspicion, though it does not mean the agent already read it. *What you can do:* handle it first; each finding comes with its concrete step.

### 2. Nivel potencial
- **Terminal.** Tú: «Potencial: probable, falta confirmar algo. No es un riesgo menor.» · Usted: «Potencial: probable, falta confirmar algo. No es un riesgo menor.» · EN: «Potential: likely, but something is unconfirmed. It is not a lesser risk.»
- **HTML (tú).** *Qué es:* existe y el agente quizá pueda llegar, pero una de las tres cosas de «comprobado» no se pudo confirmar (por ejemplo, no se sabe qué decide un hook, un programa que se ejecuta antes de cada acción del agente, no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, no una barrera real del sistema). *Qué significa para ti:* AgentReach no lo descarta ni lo confirma. No es un riesgo menor: es una pregunta abierta. *Qué puedes hacer:* lee el motivo que acompaña a cada hallazgo; resuelve lo que falta o, si el dato es delicado, trátalo como si ya fuera comprobado.
- **HTML (usted).** *Qué es:* existe y el agente quizá pueda llegar, pero una de las tres cosas de «comprobado» no se pudo confirmar (por ejemplo, no se sabe qué decide un hook, un programa que se ejecuta antes de cada acción del agente, no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, no una barrera real del sistema). *Qué significa para usted:* AgentReach no lo descarta ni lo confirma. No es un riesgo menor: es una pregunta abierta. *Qué puede hacer:* lea el motivo que acompaña a cada hallazgo; resuelva lo que falta o, si el dato es delicado, trátelo como si ya fuera comprobado.
- **HTML (EN).** *What it is:* it exists and the agent may be able to reach it, but one of the three checks behind «verified» could not be confirmed (for example, what a hook decides is unknown; a hook is a program that runs before each agent action, a permission could not be determined, or an agent rule forbids it but that rule is a platform promise, not a real system barrier). *What it means for you:* AgentReach neither rules it out nor confirms it. It is not a lesser risk: it is an open question. *What you can do:* read the reason shown with each finding; settle what is missing or, if the data is sensitive, treat it as verified.

### 3. Nivel hipótesis
- **Terminal.** Tú: «Hipótesis: indicio débil o indirecto; revísalo a mano. No es un acceso comprobado.» · Usted: «Hipótesis: indicio débil o indirecto; revíselo a mano. No es un acceso comprobado.» · EN: «Hypothesis: a weak or indirect sign; check it by hand. Not a confirmed access.»
- **HTML (tú).** *Qué es:* una señal débil o indirecta de que algo podría estar al alcance del agente. *Qué significa para ti:* es una pista, no un acceso comprobado ni un hallazgo menor que puedas ignorar sin mirar. *Qué puedes hacer:* revísalo a mano; si resulta cierto, AgentReach lo mostraría en un nivel superior.
- **HTML (usted).** *Qué es:* una señal débil o indirecta de que algo podría estar al alcance del agente. *Qué significa para usted:* es una pista, no un acceso comprobado ni un hallazgo menor que pueda ignorar sin mirar. *Qué puede hacer:* revíselo a mano; si resulta cierto, AgentReach lo mostraría en un nivel superior.
- **HTML (EN).** *What it is:* a weak or indirect sign that something might be within the agent's reach. *What it means for you:* a lead, not a confirmed access, and not a minor item to skip without looking. *What you can do:* check it by hand; if it holds, AgentReach would show it at a higher level.

### 4. No determinado
- **Terminal.** Tú: «No determinado: AgentReach no supo interpretar parte de la configuración.» · Usted: «No determinado: AgentReach no supo interpretar parte de la configuración.» · EN: «Undetermined: AgentReach could not interpret part of the configuration.»
- **HTML (tú).** *Qué es:* el nivel de un hallazgo que AgentReach no puede fijar porque la configuración del agente (la tuya o la del proyecto) incluye algo que no sabe leer, por ejemplo un hook. El reporte dice en qué archivo y qué clave, sin mostrar valores. *Qué significa para ti:* no es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook (o esa función). Por eso nada que dependa de ello puede salir «comprobado» y sale «potencial». *Qué puedes hacer:* averigua qué hace esa función; si no la escribiste tú ni la reconoces, desactívala hasta saberlo.
- **HTML (usted).** *Qué es:* el nivel de un hallazgo que AgentReach no puede fijar porque la configuración del agente (la suya o la del proyecto) incluye algo que no sabe leer, por ejemplo un hook. El reporte dice en qué archivo y qué clave, sin mostrar valores. *Qué significa para usted:* no es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook (o esa función). Por eso nada que dependa de ello puede salir «comprobado» y sale «potencial». *Qué puede hacer:* averigüe qué hace esa función; si no la escribió usted ni la reconoce, desactívela hasta saberlo.
- **HTML (EN).** *What it is:* the level of a finding AgentReach cannot set because the agent's configuration (yours or the project's) contains something it cannot read, for example a hook. The report names the file and key, never the values. *What it means for you:* neither an alarm nor a guarantee: it is a blind spot; it depends on what that hook (or feature) does. That is why nothing depending on it can be «verified»; it shows as «potential». *What you can do:* find out what that feature does; if you did not write it and do not recognize it, turn it off until you know.

### 5. No se pudo revisar
- **Terminal.** Tú: «No se pudo revisar: AgentReach no llegó a mirar esto. Es un hueco, no un veredicto.» · Usted: «No se pudo revisar: AgentReach no llegó a mirar esto. Es un hueco, no un veredicto.» · EN: «Could not check: AgentReach did not get to look here. A gap, not a verdict.»
- **HTML (tú).** *Qué es:* partes del equipo o del proyecto que AgentReach no pudo mirar por distintos motivos; por ejemplo, un archivo demasiado grande o una ubicación sensible que no activaste. *Qué significa para ti:* no sabemos qué hay ahí; no quiere decir que esté bien ni que esté mal. *Qué puedes hacer:* cada motivo trae cómo resolverlo (por ejemplo, convertir un archivo a UTF-8 o activar la revisión de esa ubicación) y después puedes volver a ejecutar.
- **HTML (usted).** *Qué es:* partes del equipo o del proyecto que AgentReach no pudo mirar por distintos motivos; por ejemplo, un archivo demasiado grande o una ubicación sensible que no activó. *Qué significa para usted:* no sabemos qué hay ahí; no quiere decir que esté bien ni que esté mal. *Qué puede hacer:* cada motivo trae cómo resolverlo (por ejemplo, convertir un archivo a UTF-8 o activar la revisión de esa ubicación) y después puede volver a ejecutar.
- **HTML (EN).** *What it is:* parts of the machine or project AgentReach could not look at, for different reasons; for example, a file that is too large or a sensitive location you did not enable. *What it means for you:* we do not know what is there; that does not mean it is fine or that it is bad. *What you can do:* each reason says how to fix it (for example, convert a file to UTF-8 or enable checking that location), and then you can run it again.

### 6. Hook
- **Terminal.** Tú: «Hook: programa que corre antes de cada acción del agente y puede bloquearla.» · Usted: «Hook: programa que corre antes de cada acción del agente y puede bloquearla.» · EN: «Hook: a program that runs before each agent action and can block it.»
- **HTML (tú).** *Qué es:* un hook es un programa que se ejecuta antes de cada acción del agente y puede aprobarla o bloquearla; puede venir de tu configuración o de la del proyecto. *Qué significa para ti:* AgentReach no sabe qué decide ese programa, así que no puede asegurar nada y por eso todo lo que depende de él sale potencial. No es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook. *Qué puedes hacer:* si lo escribiste tú, comprueba qué decide. Si viene del proyecto y no lo escribiste tú, trátalo con desconfianza y no abras el proyecto con el agente hasta revisarlo.
- **HTML (usted).** *Qué es:* un hook es un programa que se ejecuta antes de cada acción del agente y puede aprobarla o bloquearla; puede venir de su configuración o de la del proyecto. *Qué significa para usted:* AgentReach no sabe qué decide ese programa, así que no puede asegurar nada y por eso todo lo que depende de él sale potencial. No es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook. *Qué puede hacer:* si lo escribió usted, compruebe qué decide. Si viene del proyecto y no lo escribió usted, trátelo con desconfianza y no abra el proyecto con el agente hasta revisarlo.
- **HTML (EN).** *What it is:* a hook is a program that runs before each agent action and can approve or block it; it can come from your configuration or from the project's. *What it means for you:* AgentReach does not know what that program decides, so it cannot assure anything and everything depending on it shows as potential. Neither an alarm nor a guarantee: a blind spot; it depends on what that hook does. *What you can do:* if you wrote it, check what it decides. If it comes from the project and you did not write it, treat it with distrust and do not open the project with the agent until you have reviewed it.

### 7. Sandbox
- **Terminal.** Tú: «Sandbox: caja que limita lo que el agente toca; sin ella, las reglas son solo promesas.» · Usted: «Sandbox: caja que limita lo que el agente toca; sin ella, las reglas son solo promesas.» · EN: «Sandbox: a box that limits what the agent touches; without it, rules are only promises.»
- **HTML (tú).** *Qué es:* una caja aislada que limita lo que un programa puede ver y tocar. *Qué significa para ti:* sin sandbox, las reglas del agente son promesas de la plataforma, no barreras del sistema operativo. *Qué puedes hacer:* considera ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual.
- **HTML (usted).** *Qué es:* una caja aislada que limita lo que un programa puede ver y tocar. *Qué significa para usted:* sin sandbox, las reglas del agente son promesas de la plataforma, no barreras del sistema operativo. *Qué puede hacer:* considere ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual.
- **HTML (EN).** *What it is:* an isolated box that limits what a program can see and touch. *What it means for you:* without a sandbox, the agent's rules are the platform's promises, not operating-system barriers. *What you can do:* consider running the agent in an isolated environment, such as a container or a virtual machine.

### 8. Agente configurado vs analizado
- **Terminal.** Tú: «Configurado: AgentReach vio sus archivos; no sabe si se ejecutó ni qué puede alcanzar.» · Usted: «Configurado: AgentReach vio sus archivos; no sabe si se ejecutó ni qué puede alcanzar.» · EN: «Configured: AgentReach saw its files; it does not know if it ran or what it can reach.»
- **HTML (tú).** *Qué es:* tres cosas distintas. *Configurado:* existen archivos de configuración del agente. *Analizado:* AgentReach revisó qué puede alcanzar. *Usado:* el agente se ejecutó (esto AgentReach no lo sabe y nunca lo dice). *Qué significa para ti:* ver un agente en la lista no prueba que lo uses; «aún no analizado» significa que falta revisar qué puede alcanzar, no que no pueda alcanzar nada. *Qué puedes hacer:* confirma qué agentes usas de verdad; si sale «solo un indicio», compruébalo a mano.
- **HTML (usted).** *Qué es:* tres cosas distintas. *Configurado:* existen archivos de configuración del agente. *Analizado:* AgentReach revisó qué puede alcanzar. *Usado:* el agente se ejecutó (esto AgentReach no lo sabe y nunca lo dice). *Qué significa para usted:* ver un agente en la lista no prueba que lo use; «aún no analizado» significa que falta revisar qué puede alcanzar, no que no pueda alcanzar nada. *Qué puede hacer:* confirme qué agentes usa de verdad; si sale «solo un indicio», compruébelo a mano.
- **HTML (EN).** *What it is:* three different things. *Configured:* the agent's configuration files exist. *Analyzed:* AgentReach checked what it can reach. *Used:* the agent ran (AgentReach does not know this and never says it). *What it means for you:* seeing an agent listed does not prove you use it; «not analyzed yet» means what it can reach is still unchecked, not that it reaches nothing. *What you can do:* confirm which agents you really use; if it says «only a hint», check by hand.

### 9. Autocomprobación
- **Terminal.** Tú: «Autocomprobación: AgentReach revisa su propio resultado antes de imprimirlo.» · Usted: «Autocomprobación: AgentReach revisa su propio resultado antes de imprimirlo.» · EN: «Self-check: AgentReach reviews its own result before printing it.»
- **HTML (tú).** *Qué es:* antes de mostrar el reporte, AgentReach vuelve a verificar cada hallazgo (que el archivo siga existiendo, que el nivel cumpla las reglas, que el lugar señalado se pueda confirmar). *Qué significa para ti:* si uno no pasa, AgentReach lo baja de nivel en lugar de mostrar algo que no puede sostener. El aviso dice cuál hallazgo (tipo y ruta) y a qué nivel pasó. Es prudencia de la herramienta, no un fallo tuyo. *Qué puedes hacer:* nada obligatorio; si el archivo cambió mientras corría, vuelve a ejecutar.
- **HTML (usted).** *Qué es:* antes de mostrar el reporte, AgentReach vuelve a verificar cada hallazgo (que el archivo siga existiendo, que el nivel cumpla las reglas, que el lugar señalado se pueda confirmar). *Qué significa para usted:* si uno no pasa, AgentReach lo baja de nivel en lugar de mostrar algo que no puede sostener. El aviso dice cuál hallazgo (tipo y ruta) y a qué nivel pasó. Es prudencia de la herramienta, no un fallo suyo. *Qué puede hacer:* nada obligatorio; si el archivo cambió mientras corría, vuelva a ejecutar.
- **HTML (EN).** *What it is:* before showing the report, AgentReach re-verifies each finding (the file still exists, the level follows the rules, the pointed place can be confirmed). *What it means for you:* if one fails, AgentReach lowers it instead of showing something it cannot back up. The notice says which finding (type and path) and which level it moved to. It is the tool being careful, not your fault. *What you can do:* nothing required; if the file changed while it ran, run it again.

### 10. Lugar exacto no confirmado (reemplaza «línea citada»)
- **Terminal.** Tú: «No se pudo confirmar dónde está: el archivo cambió o ya no coincide.» · Usted: «No se pudo confirmar dónde está: el archivo cambió o ya no coincide.» · EN: «Could not confirm where it is: the file changed or no longer matches.»
- **HTML (tú).** *Qué es:* cada hallazgo señala un archivo y una línea; antes de imprimir, AgentReach comprueba que lo señalado siga ahí. *Qué significa para ti:* si no coincide, el hallazgo baja de nivel porque no se puede sostener con el lugar exacto. *Qué puedes hacer:* vuelve a ejecutar; si persiste, revisa ese archivo a mano.
- **HTML (usted).** *Qué es:* cada hallazgo señala un archivo y una línea; antes de imprimir, AgentReach comprueba que lo señalado siga ahí. *Qué significa para usted:* si no coincide, el hallazgo baja de nivel porque no se puede sostener con el lugar exacto. *Qué puede hacer:* vuelva a ejecutar; si persiste, revise ese archivo a mano.
- **HTML (EN).** *What it is:* each finding points to a file and a line; before printing, AgentReach checks the pointed text is still there. *What it means for you:* if it does not match, the finding is lowered because it cannot be backed with the exact place. *What you can do:* run it again; if it persists, check that file by hand.

### 11. Código de salida
- **Terminal.** Tú: «Código de salida: número que deja AgentReach al terminar; 1 si hay comprobados.» · Usted: «Código de salida: número que deja AgentReach al terminar; 1 si hay comprobados.» · EN: «Exit code: the number AgentReach leaves when it ends; 1 if there are verified findings.»
- **HTML (tú).** *Qué es:* un número que otros programas (por ejemplo, una automatización) leen al terminar AgentReach. *Qué significa para ti:* 0 = ningún hallazgo comprobado; 1 = hay hallazgos comprobados. Con `--estricto` el criterio es más exigente [ASSUMPTION: confirmar la regla exacta]. *Qué puedes hacer:* si lo usas en una automatización, haz que falle con 1.
- **HTML (usted).** *Qué es:* un número que otros programas (por ejemplo, una automatización) leen al terminar AgentReach. *Qué significa para usted:* 0 = ningún hallazgo comprobado; 1 = hay hallazgos comprobados. Con `--estricto` el criterio es más exigente [ASSUMPTION: confirmar la regla exacta]. *Qué puede hacer:* si lo usa en una automatización, haga que falle con 1.
- **HTML (EN).** *What it is:* a number other programs (for example, an automation) read when AgentReach ends. *What it means for you:* 0 = no verified findings; 1 = there are verified findings. With `--estricto` the rule is stricter [ASSUMPTION]. *What you can do:* if you use it in automation, make it fail on 1.

### 12. Camino de alcance
- **Terminal.** Tú: «Camino de alcance: cómo un agente llegaría de su carpeta a un efecto posible.» · Usted: igual · EN: «Reach route: how an agent could get from its folder to a possible effect.»
- **HTML (tú).** *Qué es:* cada hallazgo se muestra como un camino de cuatro pasos: Agente → Dónde → Qué hay → Efecto posible. Por ejemplo: un agente → `config/deploy.env`, línea 3 → un token de la nube → podría dar acceso a una cuenta de despliegue. *Qué significa para ti:* una línea continua significa que AgentReach comprobó ese paso; una línea discontinua, que no lo comprobó: es lo que podría pasar, no algo confirmado. *Qué puedes hacer:* empieza por los caminos con el trazo continuo; en los discontinuos, comprueba a mano el paso que falta.
- **HTML (usted).** Igual, con «usted»: *Qué significa para usted:* … *Qué puede hacer:* empiece por los caminos con el trazo continuo; en los discontinuos, compruebe a mano el paso que falta.
- **HTML (EN).** *What it is:* each finding is shown as a four-step route: Agent → Where → What is there → Possible effect. For example: an agent → `config/deploy.env`, line 3 → a cloud token → it could give access to a deployment account. *What it means for you:* a solid line means AgentReach checked that step; a dashed line means it did not: it is what could happen, not something confirmed. *What you can do:* start with the routes drawn in solid line; for the dashed ones, check the missing step by hand.

## Cuándo y dónde aparece cada explicación

1. **El resumen de la terminal sigue corto** (Historia 22): resumen por nivel + 3 más urgentes. No se imprime el glosario.
2. **Una frase por término, solo donde la jerga aparece.** Si hay hallazgos «potencial», sale la línea de potencial una vez; si hay un hook, la de hook; no más.
3. **Explicación completa:** `--detalle` en terminal y las fichas en el HTML.
4. **LO MÁS URGENTE** añade **una** línea «→ qué hacer» por hallazgo [ASSUMPTION].
5. **El aviso de autocomprobación dice cuál y a qué nivel:** «Se bajó a potencial: credencial en archivo, `ruta`.» (tipo y ruta, sin valores). Dependencia técnica: hoy `core/autocomprobacion.py` conoce `Correccion(ubicacion, tipo, razon, plataforma)` pero `reporting/gate.py` (l.112-113 y 260-261) solo pasa las razones y un contador, y `Correccion` no guarda nivel antes/después. La Historia 32 debe ampliar ese dato (sin valores).
6. **Sin identificadores técnicos sin explicación al lado** (`hooks.PreToolUse`, `funcion_no_modelada`, TH-n): en el resumen se muestra la frase llana y, si se muestra la clave, entre paréntesis después.
7. **HTML:** `<details>` «Cómo leer este reporte» entre `#summary` y las vistas, con las mismas fichas, un ejemplo por nivel y por agente, y un enlace «¿qué es esto?» junto a cada término que lleva a su ficha. Todos los textos propios del HTML siguen el tono elegido (hoy mezclan «usted»).
8. **README:** conserva su glosario en inglés con los mismos términos y sentido (README único en inglés, decisión de Alex).

## Key Flows

### Flow 1: Marta ve todo en «potencial» y entiende por qué
Marta, desarrolladora que usa Claude Code con un hook propio que lanza antes de cada acción.
1. Ejecuta AgentReach sobre su proyecto; responde S a las preguntas de permiso.
2. El resumen muestra 16 hallazgos en ▲ POTENCIAL y ninguno ■ COMPROBADO. Debajo, la sección «POR QUÉ HAY NIVELES NO DETERMINADO» dice: «Un hook es un programa que se ejecuta antes de cada acción del agente y puede aprobarla o bloquearla; puede venir de tu configuración o de la del proyecto» y nombra el archivo y la clave.
3. Lee: «AgentReach no sabe qué decide ese programa, así que no puede asegurar nada.»
4. **Clímax:** la frase «no es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook». Marta comprende que 16 «potencial» no son 16 peligros ni un aprobado: son lo que AgentReach no puede ver por ese hook. Revisa el hook y vuelve a ejecutar.

Falla: si Marta ejecuta con N al permiso fuera del proyecto, el resumen lo dice en una línea y no lo confunde con «no determinado».

### Flow 2: Lucía abre el HTML y usa «Cómo leer este reporte»
Lucía, líder técnica que recibe el reporte de un compañero y nunca usó la herramienta.
1. Abre el HTML (fondo claro, `--tono formal` no aplicado: tú). Ve el resumen con cuatro tarjetas de nivel.
2. No sabe qué es «hipótesis». Pulsa «¿qué es esto?» junto al nivel; se abre «Cómo leer este reporte» en esa ficha.
3. Lee «Qué es / Qué significa para ti / Qué puedes hacer» y el ejemplo de ese nivel; Escape o «volver» la deja donde estaba.
4. **Clímax:** al volver, el término ya no la frena: entiende que «potencial» no es «riesgo menor» y sabe qué revisar primero en el agente que usa.

Falla: sin JavaScript, las anclas y el `<details>` siguen funcionando.

### Flow 3: Andrés revisa una carpeta ajena en fondo claro y ancho angosto
Andrés, consultor que audita el proyecto de un cliente en una terminal de fondo blanco de 62 columnas.
1. Ejecuta AgentReach; la bienvenida se ajusta a 62 columnas sin partir palabras; la ruta del cliente va entera; «(S/N)» queda junto a su pregunta.
2. Fondo desconocido: AGENT en el texto normal de la terminal, REACH en `{colors.brand-mint-neutral}`: ambos se leen sobre blanco. Banner mediano (61 columnas).
3. El resumen muestra chips con símbolo y palabra en tonos «claro»; LO MÁS URGENTE trae una línea «→ qué hacer».
4. **Clímax:** reconoce, sin pelear con colores ni líneas cortadas, qué es lo más urgente y qué decirle al cliente, y envía el HTML con su ficha de términos.

Falla: si la terminal baja de 40 columnas o no admite Unicode, banner mínimo en ASCII y chips `[!!] [!] [?] [-]`.

## Dependencias técnicas

- Autocomprobación: ampliar `Correccion` con nivel antes/después y pasar tipo y ruta a `reporting/gate.py` y a la vista.
- Catálogo por concepto: hoy el catálogo se indexa por tipo de hallazgo y por motivo; hace falta un catálogo de términos (11 fichas) con ES (tú/usted) y EN, más una prueba de cobertura término-contra-entrada y de ausencia de «seguro» / «sin riesgo».
- `LO MÁS URGENTE`: obtener la línea «qué hacer» del catálogo existente (`COMO_RESOLVER`).
- Plantilla HTML: claves propias de los textos de «Cómo leer este reporte» y de «¿qué es esto?» en ES (tú/usted) y EN; retirar el «usted» fijo.

## Open Questions / [ASSUMPTION]

1. **[ASSUMPTION, pendiente de Alex]** Fórmula neutra para «no determinado por un hook»: «no es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook», en lugar de «no significa que sea inseguro».
2. **[ASSUMPTION]** LO MÁS URGENTE añade una línea «→ qué hacer» por hallazgo.
3. **[ASSUMPTION]** El conjunto de términos pasa a 11: se añaden «lugar exacto no confirmado» (que reemplaza «línea citada») y «código de salida».
4. **[ASSUMPTION]** Valores de `--tema` (`claro|oscuro|auto`) y que `auto` no pinta fondo.
5. **[ASSUMPTION]** La terminal informa la ruta del HTML; no lo abre sola.
6. **[ASSUMPTION]** La vista Imprimir incluye las fichas de los términos presentes, con los `<details>` abiertos.
7. **[ASSUMPTION]** Regla exacta del código de salida con `--estricto` (no se leyó el código; solo se afirma 0/1 por comprobados).
8. **[ASSUMPTION]** La frase de autocomprobación («Se bajó a potencial: …») y el formato de «qué hacer» se afinan al redactar el catálogo; las líneas de terminal de este documento son propuestas.
9. **[ASSUMPTION]** Una explicación única de hook cuando hay muchos «no determinado», con el resto por referencia.
10. Abierta: cómo presentar el límite conocido de rutas con espacios largas que se parten entre palabras.
11. Abierta: Historia 31 (detectar el fondo real, OSC 11) cambiará el logo y los tonos «claro/oscuro» de desconocido a conocido.
