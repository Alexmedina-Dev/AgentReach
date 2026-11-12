# Extracto: qué explica hoy AgentReach en lenguaje llano (y qué falta)

Solo lectura. Citas literales entre comillas; formato archivo:línea.

## 1. README.md (en inglés; no existe versión en español)

- Hallazgo (finding), README.md:59: "A finding is one item the agent could access. Each finding has evidence, a location, and a confidence level."
- Niveles, README.md:113-117:
  - Verified: "Three things are true at the same time. The file exists. The system permissions allow the person who runs the agent to read it. No rule of the agent blocks it."
  - Potential: "The item exists and the agent might access it, but one of the three things could not be confirmed."
  - Hypothesis: "A weak or indirect sign that you should check manually."
  - Aviso propio, README.md:120: "The exact special cases will be refined in the PRD".
- Caminos (Reach paths), README.md:124-128: "**Agent → Where → What is there → Possible effect**"; "A solid line means AgentReach checked that step. A dashed line means it did **not** check it".
- Regla que baja nivel, README.md:136: "AgentReach does not guess: it lowers the level to Potential and says so."
- Configurado vs usado, README.md:97: "It says *configured*, not *used*"; "'could not determine' is a valid answer".
- Reporte por terminal, README.md:182: ocho campos, "a fixed section with what AgentReach **could not check**"; "A level of 'potential' always says why it is not 'verified'."
- Permisos en dos niveles, README.md:245 (párrafo único y denso): "with N nothing outside the project is read and the levels that depend on the rules stay at 'potential'".
- Glosario (README.md:140-157): MVP, In testing, AI agent, Access, Finding, Repository, Symlink, Junction, Permissions/ACL, Environment variable, Token/credential, SSH key, Sandbox ("An isolated environment that limits what a program can see..."), Core, Adapter, Opt-in.
- Explicado en línea: MCP ("connections between the agent and external tools", README.md:71), `--tarea` (":100"), wheel (:189), uv (:193).
- NO está en el README: hook, "no determinado", autocomprobación, "no modela", línea citada, "ajeno a la tarea" (solo se nombra en :100 y :182), código de salida, `--detalle` (solo en :245 sin explicar), tono tú/usted.

## 2. core/catalogo_explicaciones.py y contracts/finding.py

Estructura:
- Los textos largos viven en `contracts/finding.py:281` (`CATALOGO_EXPLICACIONES: dict[Tipo, dict[Idioma, tuple[str, str]]]`): 20 tipos (TH-1 a TH-20) x ES/EN x (qué significa, qué hacer). Esos ES son de tuteo ("tú").
- `catalogo_explicaciones.py` agrega: `TITULO_TIPO` (20, ES/EN, :45), `TITULO_MOTIVO` (12 motivos de "no se pudo revisar", :83), `COMO_RESOLVER` (12, ES/EN, :107), `PROVEEDOR` (:147), `POSTURA` (:160), `AJENO` (:168), `NIVEL` (solo la palabra: COMPROBADO/POTENCIAL/HIPÓTESIS, :174), `LIMITES` (6, ES/EN, :181) y `LIMITES_TAMBIEN` (:199).
- Tono: `Tono.CERCANO` (tú, por defecto) y `Tono.FORMAL` (usted, :215). `EXPLICACIONES_FORMAL` (:223) y `COMO_RESOLVER_FORMAL` (:250) reescriben solo lo que lleva pronombre. En inglés el tono no cambia el texto (:216). Opción `--tono` en cli/__init__.py:227.
- Nunca viene de un modelo de lenguaje (:3).
- Motivo del nivel ("por qué"): `_TEXTO_MOTIVO` en finding.py:485, p. ej. "Existe, el sistema operativo permite leerlo y ninguna regla del agente lo impide"; "Protegido por política del agente, no por barrera del sistema operativo"; "No determinado".

Tres ejemplos reales (ES, tuteo):
1. Credencial en archivo (finding.py:284-285). Significa: "Un archivo del proyecto guarda una credencial (una clave o contraseña que da acceso a un servicio). Un agente que pueda leer el proyecto podría leerla." Hacer: "Saca la credencial del proyecto o guárdala en un gestor de secretos (un programa que guarda claves cifradas) y rótala (rotar es cambiarla por una nueva y desactivar la vieja) si estuvo expuesta."
2. Sin sandbox (finding.py:374-375). Significa: "La plataforma no tiene sandbox (una caja que limita lo que el agente puede tocar): las reglas son promesas de la plataforma, no barreras del sistema operativo." Hacer: "Considera ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual."
3. Hook o MCP de comando (finding.py:414-415). Significa: "La configuración del proyecto define un hook (comando que una herramienta lanza sola ante un evento) o un servidor MCP (conexión del agente con herramientas externas) que arranca un programa cuando ocurre un evento..." Hacer: "Revisa ese comando y desactiva el que no reconozcas antes de abrir el proyecto."

Conceptos SIN entrada propia (no hay clave de glosario; el catálogo solo está indexado por tipo de hallazgo y por motivo de "no revisado"):
- Los tres niveles: solo existe el nombre (`NIVEL`) y el motivo por hallazgo; la definición en español solo está como `LV_MEAN` en el HTML (ver 4). No hay "qué hacer con cada nivel".
- "No determinado" (`Postura.NO_DETERMINADA`, `Ajeno.NO_DETERMINADO`, `Motivo.NO_DETERMINADO`): solo rótulos de una palabra.
- hook, sandbox, shell, MCP, rotar, gestor de secretos, Unicode: no tienen entrada, pero SÍ se explican entre paréntesis dentro de los textos de TH-1, TH-8, TH-10, TH-12, TH-14. Esa explicación solo aparece si el hallazgo concreto está en el reporte y se repite (o se omite con "igual que el hallazgo de la línea N").
- Agente configurado vs analizado: solo `cfg_*` en texto.py (ver 3), no en el catálogo.
- Autocomprobación: ninguna entrada.
- Código de salida, `--detalle`, línea citada, "regla" vs "postura": ninguna.

## 3. reporting/texto.py (terminal)

Orden del resumen corto (`_pasada`, :525-542): encabezado, RESUMEN, AGENTES CONFIGURADOS, POR QUÉ HAY NIVELES «NO DETERMINADO», LO MÁS URGENTE, alcance, cierre.

Textos ES literales (diccionario `_T`):
- RESUMEN (:65, :284): "RESUMEN  (N archivos mirados)". Frases por nivel (:68-75): "exposición confirmada; se atiende primero" / "probable, falta confirmar algo; revisar pronto" / "sugerencias, no accesos comprobados" / "huecos de cobertura, no un veredicto". Solo salen niveles con conteo > 0 (:290).
- AGENTES CONFIGURADOS (:134-143): "Según los archivos de configuración que existen. No significa que el agente se haya ejecutado."; "configurado" / "probablemente configurado" / "solo un indicio"; "AgentReach aún no analiza qué puede alcanzar"; "marco instalado sobre {sobre}"; "No determinado: {ruta} lo leen varios agentes ({candidatos}); no dice cuál está configurado."
- POR QUÉ HAY NIVELES «NO DETERMINADO» (:147-153): "AgentReach no pudo interpretar esto en la configuración del agente. Mientras no lo interprete no puede dar un nivel «comprobado» a lo que depende de ello (se muestra sin valores, solo el archivo y la clave):", seguido de ruta · clave y TITULO_MOTIVO (p. ej. "Función de la configuración que AgentReach no modela") y "→ {cómo resolver}". Solo aparece si hay hallazgos no determinados y causas (:394).
- LO MÁS URGENTE (:154-155, :422): "LO MÁS URGENTE  (3 de 5)", cada uno: símbolo, nivel, agente, título corto, y "ruta:línea". Sin "por qué" ni "qué hacer".
- Autocomprobación (:122-128, :296-299): "Antes de imprimir se corrigieron {n} hallazgo(s) porque no pasaron la autocomprobación ({razones})." Razones: "regla de nivel violada", "el archivo ya no existe", "la línea citada no se pudo confirmar".
- Cierre (:156-157): "Esto cubre solo lo que AgentReach pudo revisar. No significa que lo demás sea seguro: lo que no se pudo revisar y los límites están en el reporte visual y en --detalle." Más "Código de salida: 1 (hay hallazgos comprobados)" (:129-133) y "Para ver el listado completo, con códigos y motivos técnicos, ejecuta con --detalle." (:162).

Jerga sin explicar en estas pantallas: "no modela" (TITULO_MOTIVO), "línea citada", "autocomprobación", "regla de nivel violada", "marco instalado sobre", "esquema de configuración 2.x" (:187-192), la clave técnica de la causa (p. ej. `hooks.PreToolUse`; viene del adaptador en `c.clave`, texto.py:403, no está en el catálogo), "Código de salida", "--estricto" (:133), "Reglas del agente", "Ajeno a la tarea", "postura" (lo que se muestra: "lo permite", "pide confirmación", "lo bloquea (solo por regla)").

¿El aviso de autocomprobación sabe CUÁL hallazgo cambió? En core/autocomprobacion.py: `Correccion(ubicacion, tipo, razon, plataforma)` (:48-52) y `RazonCorreccion` con 3 valores (:41-44). Pero `reporting/gate.py:112-113,260-261` solo pasa a la vista `correcciones: tuple[RazonCorreccion]` y `hallazgos_corregidos: int` (cuenta por (ubicacion, tipo), :261). Es decir: el dato de ubicación y tipo EXISTE en el núcleo pero se descarta antes del reporte. El aviso no dice cuál ni en qué cambió (a qué nivel pasó); no hay campo de "nivel antes/después" en `Correccion`.

## 4. reporting/plantilla_reporte.html

- Leyenda de niveles `ul.lvlegend` (CSS :260-263; se arma en :1011): por cada nivel del agente, ícono + nombre + `AG.meaning[l]`, más "no se pudo revisar". Textos `LV_MEAN` (:650-652): "Confirmado: el agente puede llegar hoy." / "Probablemente alcanzable; falta confirmar algo." / "Solo una sugerencia. No es un acceso comprobado." Nota `LEVEL_NOTE` (:653): "Los niveles son solo de este agente; nunca se mezclan con los de otro."
- Campo "Qué significa": ocho campos `T_.f` (:733/:775; el 8.º es "Qué significa / What it means") con el texto `que_significa(...)` del catálogo (html.py:154). Cada hallazgo se despliega con "Detalles" (`T_.details`).
- Camino: `T_.cols` = Agente, Dónde, Qué es, Efecto posible; `T_.colsub` = quién actúa, carpeta o archivo línea, qué hay, no comprobado (:760-761); `lgSolid`/`lgDash` (:762); `chainV`/`chainO` (:777-778); `via` (:786); `ruleNote` (:790).
- "No determinado": existe un aviso `T_.ndNote(n, items)` (:750): "{n} hallazgos no tienen nivel determinado, por eso ninguno puede ser Comprobado. AgentReach no interpreta: {items}." (banner `nb` en :1202). No hay sección propia ni explicación del porqué.
- Agentes configurados (sección `#cfg`, :549, :1089-1098): `T_.cfgTitle`, `cfgNote` ("AgentReach vio archivos de configuración; no sabe si este agente se ejecutó."), `undetTitle`/`undetText`, `confBadge`.
- Límites (`#limits`, :601; `limTitle`, `limLead`: "Esta sección siempre aparece. Que no haya hallazgos no significa que no haya riesgo."; `partFolder`, `partTool`, `fix`).
- Otras: `lead` (:751), `kbd` (atajos y navegación, :769), `foot` (:781), `panelHint` (:771), `radarCap`.
- Organización: pestañas por agente (`#tabs`, role=tablist, :553, :1183); vistas por botones `['graph','table','list','print']` = Recorrido, Tabla, Lista, Imprimir (:1171; rótulos :753); barra de filtros (carpeta, tipo, búsqueda); `#summary` con KPIs (:557, :1194); `#cfg` (:549); `#graphView`, `#tableView`, `#listView`, `#printView` (:580-597); panel lateral `#panel` (:590); `#limits` al final (:601). Hay `<details class="fold">` ya usado (:1076) y `<details>` en límites (:1108): el patrón plegable existe.
- Dónde cabría "Cómo leer este reporte": entre `#summary` (:557) y las vistas (:580), o dentro de `#legend`/`#legend2` (:583, :595), o como `<details>` justo antes de `#cfg`. Debe tener T_ propias en ES y EN (p. ej. `T_.howTitle`, `T_.howBody`; hoy NO existen). La vista Imprimir arma su propio texto (:1139-1151); habría que decidir si lo incluye.
- Idioma: ES/EN con `lang`; tono: el HTML usa `tono` solo para "qué significa/qué hacer" (html.py:154); los textos propios de la plantilla usan "usted" (p. ej. "Elija un camino", ":771").

## 5. Reglas de diseño que condicionan un texto explicativo

docs/reporte-terminal/diseno.md:
- Resumen arriba y corto (:32): "cuántos archivos se miraron y un conteo por nivel... cada uno con su símbolo, su palabra y una descripción corta".
- Ancho: ":84" `W = clamp(columnas, 60, 100)`; nunca cortar rutas (:87); medir ancho visible (:89); si la terminal es <60 se usa 60 (:91).
- Tono: P3 (:17) proponía "usted" en terminal; hoy el tono es configurable (`--tono`, default cercano/tú; cli:227). El diseño nota la inconsistencia (:264).
- Sin códigos en pantalla sin --detalle (:274 prueba 6; :56): TH-n e identificadores solo con `--detalle`.
- Símbolos con respaldo ASCII: `[!!]`, `[!]`, `[?]`, `[-]`, `->` (:127); `--ascii` / `AGENTREACH_ASCII=1` (:140). Siempre símbolo y palabra (:271).
- Salida escrita de una vez (:125); el nombre de los interruptores no se traduce (:153).
- Sección 8 (:262): el propio diseño ya listó "Palabras que un novato no entiende y no se explican": "rote la clave", "gestor de secretos", "ask / deny", "Unicode", "shell", "mínimo privilegio".

docs/presentacion-terminal/diseno.md:
- Sin emojis (D2, :188): "No. En consolas de Windows antiguas salen como cuadros o signos de interrogación y rompen el ancho".
- Tono D1 (:187): "Usted", también en `doctor` y preguntas (hoy el código usa tú por defecto: contradicción documental).
- Funciona en la consola más pobre, respaldo ASCII sin tildes (:32); degradación bajo 60 columnas (:181).
- Banner por ancho W; la terminal es una herramienta interactiva con S/N.

## Brechas (lo que un usuario no experto no puede entender hoy)

1. No existe glosario ni "Cómo leer este reporte" en el HTML ni en la terminal; el único glosario está en el README, en inglés.
2. El README (la única definición completa de los tres niveles) no está en español, y el reporte solo da una frase corta por nivel; ninguna explica la diferencia práctica ni qué hacer con cada uno.
3. "Potencial no quiere decir riesgo menor" solo sale en el detalle completo (texto.py:79), no en el resumen corto.
4. "No determinado" aparece sin definición: el resumen corto lo cita, y dentro de la causa salen términos como "no modela", "hooks.PreToolUse" (clave técnica cruda, texto.py:403).
5. Hook, sandbox, shell, MCP y rotar se explican solo entre paréntesis y solo si ese tipo de hallazgo aparece; no hay explicación a demanda.
6. "Agente configurado" frente a "analizado" frente a "usado": una frase corta (texto.py:137) y un "AgentReach aún no analiza qué puede alcanzar" que no dice qué implica.
7. Autocomprobación: el usuario ve "se corrigieron N hallazgo(s)" sin saber cuál, qué cambió ni si debe preocuparse; el núcleo conoce `ubicacion` y `tipo` pero el reporte los descarta (gate.py:261).
8. "Línea citada", "regla de nivel violada" y "esquema de configuración 2.x" son jerga interna.
9. LO MÁS URGENTE no incluye "qué significa" ni "qué hacer"; solo título corto y ruta. El usuario debe ir a `--detalle` o al HTML, y el cierre lo menciona sin explicar qué es `--detalle`.
10. Código de salida y `--estricto` sin explicar en lenguaje llano.
11. Cierre corto: "no significa que lo demás sea seguro" es la única advertencia de límites en la terminal; los 6 límites solo salen completos con `--detalle`.
12. Inconsistencia de tono: el diseño docs dice "usted" (D1, P3), el catálogo y el CLI usan "tú" por defecto, el HTML mezcla "usted" en la plantilla y tú/usted según `--tono` en el catálogo.
13. Sin ayuda en el momento: no hay enlace ni indicación "qué es esto" junto a cada término; el catálogo solo se indexa por tipo de hallazgo y motivo, no por concepto.
14. Los dos documentos de diseño (:262 de reporte-terminal) ya señalan palabras sin explicar ("mínimo privilegio", "ask / deny", "Unicode") y no hay evidencia en lo leído de que se hayan resuelto todas.
