---
type: analisis-producto-seguridad
topic: Mejoras NUEVAS para AgentReach a partir del reporte del 2026-11-12 (proyecto real local) y del código
complementa: sprint-change-proposal-2026-11-11.md (R1 a R8, historias 37 a 42) y research/technical-agentreach-reporte-proyecto-real-local-2026-11-11/research.md
created: 2026-11-12
status: borrador para decisión de Alex
---

# Análisis profundo de AgentReach: mejoras nuevas (2026-11-12)

## Cómo leer este documento

- **Hecho verificado**: lo comprobé yo hoy contra los datos embebidos del reporte (`agentreach-20261112-093754-...html`), contra el código (archivo:línea) o midiendo con una prueba de solo lectura. **Hipótesis**: tiene lógica pero falta evidencia.
- No repito R1 a R8 ni las historias 37 a 42 (repetidos entre agentes, `ORCA_PANE_KEY`, caja de efecto vacía, opencode sin señales, `--redact-paths`, `lang`/idioma, «Cómo leer» en corto, avance al revisar). Cuando una mejora toca una de ellas, lo digo.
- No leí ningún `.env`. Solo usé nombres de archivo, tamaños y metadatos, y las rutas que ya muestra el reporte. Ningún valor de secreto aparece aquí.
- Regla que guía todo: **ninguna mejora sube un nivel**. Las que tocan el nivel solo cambian lo que se explica, el orden o la agrupación (SM-1 intacta).

## Qué cambió entre la corrida de ayer (17:33) y la de hoy (09:37)

Hechos verificados con un script de comparación sobre los dos JSON:

| Dato | Ayer | Hoy |
|---|---|---|
| Archivos recorridos | 2089 | 2099 |
| Hallazgos | 12 | 14 (nuevo: `.env` línea 10, tipo TH-1, proveedor «desconocido», en Claude Code y en opencode) |
| No se pudo revisar | 24 | 25 (nuevo: un segundo pack de `.git`, `pack-18ad57...`) |
| Comprobado / Potencial / Hipótesis | 0 / 10 / 2 | 0 / 12 / 2 |

Lectura: el proyecto cambió entre una corrida y otra y AgentReach **no lo dice**; hay que comparar a ojo (ver mejora 9).

## Resumen: 11 mejoras ordenadas por valor/esfuerzo

| # | Mejora | Frente | Esfuerzo | Decisión de Alex | Estado de la evidencia |
|---|---|---|---|---|---|
| 1 | «Qué hacer primero»: orden de atención y agrupar 14 hallazgos en 7 acciones | Utilidad | M | Sí (criterio de orden) | Hecho |
| 2 | Depurar «No se pudo revisar»: de 25 filas a 5, y corregir el «más de 5 MB» falso | Cobertura | S | Poca (tope de tamaño) | Hecho |
| 3 | TH-14: mostrar si es hook, servidor MCP o salto de permisos (dato que ya se calcula y se pierde) | Utilidad | S | No | Hecho |
| 4 | `.claude/settings*.json` queda en «Sin agente específico» y no aparece en la pestaña de Claude Code | Precisión | S | No (revisión de Winston) | Hecho (el dato); hipótesis (que sea un descuido) |
| 5 | Decir las dos causas apiladas del «No determinado» (la 2.ª es el tope de AD-11) | Precisión | S | No | Hecho |
| 6 | Un solo recorrido del árbol en vez de seis (medido: 3,1 s solo de recorrer 2099 archivos) | Experiencia | S | No (podar dependencias: sí) | Hecho (medición); hipótesis (proyectos con `node_modules`) |
| 7 | La evidencia de «configurados» se trunca a 3 sin avisar (cierra la pregunta pendiente R7b) | Experiencia | S | No | Hecho |
| 8 | Ubicaciones sensibles: 10 filas para 2 funciones, 6 de ellas inexistentes aquí; ofrecer activarlas en la misma ejecución | Experiencia | M | **Sí** (cambia AD-9) | Hecho |
| 9 | «Qué cambió desde la última revisión» (diferencia entre dos reportes) | Experiencia | M | **Sí** (leer fuera del proyecto) | Hecho (la necesidad); hipótesis (el diseño) |
| 10 | Claves privadas dentro del proyecto (`.pem`, `.key`, `id_rsa`, `.tfstate`) no se detectan ni se mencionan | Cobertura | M | **Sí** (amplía el catálogo) | Hecho (probado); hipótesis (que importe aquí) |
| 11 | Usar `.gitignore` como contexto de la acción de TH-1 (sin afirmar nada sobre git) | Utilidad | L | **Sí** | Hipótesis |

---

## 1. «Qué hacer primero»: orden de atención y agrupar por archivo

**Problema (hecho).** El cuadro «Corregir primero» (`plantilla_reporte.html:1236`, `renderSummary`) toma `AG.levels[0]`, que es *Comprobado*, y lista solo hallazgos de ese nivel. Como TH-1 por nombre no pasa de Potencial (AD-11, `FUENTE_VERIFICADA` es falso para todos), el cuadro **está vacío por diseño** en cualquier corrida real: muestra «No hay hallazgos Comprobados para este agente. Mire el siguiente nivel» (`startNone`, líneas 738 y 780). El reporte de hoy tiene 14 hallazgos y 0 acciones sugeridas arriba. Además:
- Las opciones de agrupar son `none`, `folder`, `type`, `level` (línea 1063); no hay «por archivo». Los 14 hallazgos son **7 pares archivo+tipo**: `.env` TH-1 (8 filas: 4 líneas × 2 agentes), TH-10, `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json` (TH-14), y 2 variables TH-4.
- La acción de TH-1 («Saca la credencial del proyecto o guárdala en un gestor de secretos y rótala») es igual para las 4 líneas; el reporte no dice cuál de las 4 atender antes.

**Propuesta.** (a) Reemplazar «Corregir primero» por **«Por dónde empezar»** con orden de atención sin tocar el nivel. Criterio fijo y explicable, por ejemplo: tipo que da acceso a un servicio externo (TH-1, TH-3) antes que configuración que ejecuta (TH-14) antes que condiciones de plataforma (TH-10) antes que variables de entorno (TH-4); a igualdad, proveedor «firma» o de nube antes que «desconocido». (b) Agregar agrupar por **archivo** y mostrar «7 acciones» además de «14 hallazgos». (c) Rotularlo «orden de atención, no certeza» para no confundirlo con el nivel.

**Toca:** FR-9 campo 7 («qué hacer»), FR-12, FR-11; AD-16 (catálogo fijo), AD-17 (datos del HTML), AD-15 (el orden se calcula sobre la vista de la compuerta). **Esfuerzo:** M (plantilla y vista; el orden es una tabla fija). **Riesgo SM-1:** nulo si el rótulo lo aclara; el nivel no cambia. **SM-2:** nulo (solo campos ya permitidos). **Decisión de Alex:** sí, el criterio de orden es un juicio de producto (¿una base de datos va antes o después de una firma de tokens?). **Relación con historias:** la 37 («también en») reduce filas; esta ordena y agrupa lo que queda, y no las duplica.

## 2. Depurar «No se pudo revisar» y corregir el «más de 5 MB»

**Problema (hecho).** Las 25 entradas se reparten así: 1 `~/.claude/settings.json` (valioso: hooks `PreToolUse`), 1 `.git` (historial, fase 2), **2 packs de `.git`**, **11 `.docx`**, **10 ubicaciones sensibles** (ver mejora 8).

- **El texto es falso.** Cada entrada de tamaño dice «Archivo demasiado grande (más de 5 MB)» (`catalog.no_review.archivo_demasiado_grande`). El tope real que usa el recorrido es **1 MiB** (`contracts/ports.py:22`, usado en `collectors/enlaces.py:117`); el de 5 MiB es el de `leer_seguro`. Medí los tamaños: de los 13 archivos marcados, **7 pesan entre 1,5 y 4,0 MB** (por ejemplo 1,57 MB, 2,16 MB, 2,29 MB, 2,56 MB, 2,71 MB, 3,32 MB, 4,00 MB). Solo 6 superan 5 MB (6,1 a 32,4 MB). Es una afirmación incorrecta en un reporte de seguridad. (Los dos topes distintos fueron intencionales según `spec-historia-4b-lectura-segura.md:70`, pero el texto al usuario no los distingue; AD-14 y FR-26 solo mencionan 5 MB.)
- **Los `.docx` nunca habrían sido leídos aunque fueran pequeños.** `clase_de_archivo` (`collectors/detector/archivos.py:45-66`) solo abre `.env*`, `.npmrc`, `credentials.json` y extensiones de texto; `.docx` no está. Se marcan «no revisados» únicamente porque `recorrer` agrega `ARCHIVO_DEMASIADO_GRANDE` a **todo** archivo de más de 1 MiB sin mirar si algún detector lo abriría (`enlaces.py:116-118`; `archivos_repo.py:47` lo copia tal cual). Un `.docx` de 900 KB, un `.xlsx` (hay 4, uno se llama `Nomina.xlsx`) o un PDF (hay uno) **no aparecen en ninguna parte**. La cobertura declarada es incoherente: lo grande se anuncia, lo pequeño se calla. FR-25 dice «solo se usa cuando de verdad no se pudo mirar».
- **Los packs de `.git` no aportan nada.** `.git` ya está como entrada propia y el contenido de `.git` se excluye a propósito (`archivos.py:54`, `contexto.py:42`); el tercer pack (575 KB) no sale porque pesa menos de 1 MiB, lo que prueba que la entrada depende del tamaño y no de un riesgo.
- Las listas de límites (FR-21) no dicen que **no se leen formatos binarios ni de ofimática** (docx, xlsx, pdf, imágenes) ni datos personales: son 6 límites más «también no revisados», y ninguno lo menciona (verificado en `limits.es` y `limits_also.es` del JSON).

**Propuesta.**
1. Cambiar el texto a «supera el tope de lectura (1 MiB)» o unificar el tope; el número debe salir de la constante, no escrito a mano.
2. Marcar «demasiado grande» solo cuando el archivo habría sido candidato a abrirse (por nombre/extensión). Los demás formatos no abiertos pasan a **una sola línea agrupada** por extensión y cantidad, sin nombres: «20 documentos de ofimática y PDF (docx, xlsx, pdf) no se leen: formato que AgentReach no analiza». Eso además ayuda a R5/`--redact-paths`, porque hoy los nombres de reuniones con clientes salen como filas.
3. No listar packs bajo `.git` (la fila `.git` ya los cubre).
4. Agregar un límite 7 en FR-21: «No se leen documentos de ofimática, PDF ni imágenes, ni datos personales: AgentReach busca credenciales y configuración».

Resultado esperado con el reporte de hoy: **25 filas pasan a 5** (settings de usuario, `.git`, documentos no leídos, y 2 de ubicaciones sensibles agrupadas, ver mejora 8). Esto responde la pregunta pendiente R7(a): con esta limpieza no hace falta un filtro de «No se pudo revisar»; la sección alcanza.

**Alternativa evaluada y descartada (hipótesis):** abrir los `.docx` con `zipfile` y buscar credenciales en su texto. Cumpliría solo lectura y sin red, pero exige defensa contra *zip bombs* y XML hostil, y el detector actual busca asignaciones `NOMBRE=valor` que en notas de reuniones casi no aparecen. Poco valor por riesgo. No lo propongo.

**Toca:** FR-25, FR-26, FR-20, FR-21; AD-14 (lista cerrada de 12 motivos: se necesitaría un motivo nuevo del tipo «formato no analizado», que **es** un cambio de lista cerrada), AD-16 (catálogo ES/EN). **Esfuerzo:** S. **Riesgo SM-1:** nulo. **SM-2:** mejora (menos nombres de archivo en pantalla). **Decisión de Alex:** poca; solo si el motivo nuevo en la lista cerrada le parece bien.

## 3. TH-14: decir si es hook, servidor MCP o salto de permisos

**Problema (hecho).** Los 3 hallazgos TH-14 (`.claude/settings.json:2`, `.claude/settings.local.json:2`, `.mcp.json:5`) llevan el mismo texto: «define un hook **o** un servidor MCP», y la acción «revisa ese comando» sin decir cuál. Sin embargo `config_ejecuta_sola.py` ya calcula la distinción: `self.rotulos` asocia cada hallazgo con «hooks», «mcp» o «salto_de_permisos» (líneas 12, 56-58, 70, 138). **Nada consume `rotulos`** (búsqueda en todo `src/agentreach`: solo aparece en ese archivo y en una función local no relacionada de `html.py:179`). El dato se calcula y se tira en `app/auditar.py`. La alerta más relevante para quien abre una carpeta ajena, que un hook se ejecute solo, no se distingue de un servidor MCP.

**Propuesta.** Pasar el rótulo (lista fija de 3 a 4 valores) hasta la vista de la compuerta y usar textos distintos del catálogo (la versión «corregida» que el propio docstring del módulo dice que existe). Para hooks puede añadirse el **nombre del evento** de una lista fija (`SessionStart`, `PreToolUse`…), nunca el comando.

**Toca:** FR-11, FR-18 (TH-14), FR-3 (el comando no se copia: se mantiene); AD-1 (el campo nuevo debe ser enumeración cerrada, no texto libre), AD-15, AD-16. **Esfuerzo:** S. **SM-1:** nulo. **SM-2:** nulo si es enumeración cerrada; la prueba canario debe cubrir un hook con marca. **Decisión de Alex:** no.

## 4. `.claude/settings*.json` aparece en «Sin agente específico»

**Problema (hecho en los datos).** `na-0` (`.claude/settings.json:2`) y `na-1` (`.claude/settings.local.json:2`) tienen `agent=null` y viven en el grupo «Sin agente específico». Son archivos propios de Claude Code (el agente está `analyzed=true`, confianza alta, con esos mismos archivos como evidencia en `configured_agents`). La pestaña «Claude Code» solo muestra 5 hallazgos (TH-10 y las 4 líneas de `.env`) y **esconde los hooks**, justo lo que más importa de ese agente. **Hipótesis:** la regla de AD-12/FR-31 («los nombres compartidos no identifican un agente») se aplicó a `.mcp.json` (correcto, es compartido) y se extendió sin querer a una ruta que sí es exclusiva de Claude Code.

**Propuesta.** Atribuir al agente los hallazgos de rutas que el catálogo de agentes marca como firma fuerte de un solo agente (`.claude/**`), manteniendo `.mcp.json`, `.vscode`, `.github`, `.env` como compartidos. Una línea de prueba: `.claude/settings.json` cae en la pestaña de Claude Code.

**Toca:** FR-31, FR-17 (un reporte por agente), AD-12, AD-18. **Esfuerzo:** S (más pruebas del oráculo, que podrían cambiar el agente esperado de casos existentes: revisar). **SM-1:** nulo (no toca nivel). **Decisión de Alex:** no; conviene que Winston confirme que no contradice AD-12.

## 5. Decir las dos causas apiladas del «No determinado»

**Problema (hecho).** El reporte dice, para los 4 TH-1 de Claude Code (`reason=no_determinado`): «no tienen nivel determinado, por eso ninguno puede ser Comprobado. AgentReach no interpreta: `~/.claude/settings.json · hooks.PreToolUse`» (`ndNote`, plantilla línea 729/771). Eso insinúa que modelar ese hook los dejaría subir. El código muestra lo contrario: `core/nivel.py:74-78` corta con «no determinado» **antes** de llegar a `nivel.py:98-100`, donde un tipo por nombre sin fuente verificada se queda en Potencial con `SIN_FUENTE_VERIFICADA`. La causa 2 (tope de AD-11) queda **tapada** por la causa 1. La propuesta aprobada (anotar R1 en la Fase 2) corrige el PRD pero el **texto que ve la persona** sigue sugiriendo lo que el PRD niega.

**Propuesta.** Cuando el motivo es `no_determinado` y el tipo tiene tope por fuente, el reporte agrega una frase fija: «Aunque AgentReach interpretara esa configuración, este hallazgo seguiría en Potencial: el nombre del archivo basta para sospechar una credencial, no para probar que sea real». Se obtiene recalculando `calcular()` con postura conocida (función pura, solo para el texto), sin cambiar el nivel mostrado.

**Toca:** FR-32, FR-7, SM-8 (SM-C3: no inflar la medición), AD-11, AD-12. **Esfuerzo:** S. **SM-1:** nulo, y de hecho lo refuerza (el reporte deja de sugerir que algo podría ser Comprobado). **Decisión de Alex:** no.

## 6. Un solo recorrido del árbol

**Problema (hecho, con medición).** `recorrer()` se llama 6 veces por auditoría: `enlaces.py:139` (TH-6), `archivos_repo.py:47`, `contexto.py:107`, `despliegue.py:46`, `invisibles.py:215` y de nuevo en `app/auditar.py:187`. Cada llamada hace `scandir` y varias consultas por entrada (`_es_enlace` se llama dos veces por entrada: `fs_solo_lectura.py:107` y `:63`). Medí sobre la carpeta del reporte (solo metadatos, sin abrir contenido): **0,52 s por recorrido, 3,11 s los seis**, para 2099 archivos; además, abrir los 1716 archivos de texto una sola vez tarda **2,4 s**. El recorrido no poda nada: `recorrer` no excluye `.git`, `node_modules` ni `.venv` (los excluyen después cada detector). `files_looked_at=2099` incluye 57 archivos de `.git`, que nunca se analizan; se presenta como «archivos mirados».
- **Hipótesis (no medida):** en un proyecto con `node_modules` de decenas de miles de archivos, el tiempo se multiplica por seis. Esto explica por qué la sensación de espera (que ya motivó la historia 41) no es solo de presentación.

**Propuesta.** Calcular `recorrer` una vez por auditoría y compartir el resultado (solo metadatos; el contenido **no** se guarda, para no romper el «el contenido no sobrevive al análisis» de los detectores). Opcional y a decidir: podar `.git`/`node_modules`/`.venv` en el recorrido compartido mostrando «N carpetas de dependencias no recorridas» (hoy `node_modules` puede contener enlaces que TH-6 sí ve; podar es una compensación cobertura/tiempo). Renombrar el contador a «archivos recorridos».

**Toca:** AD-3 (recorrido), AD-14, AD-17 (contador), FR-20. **Esfuerzo:** S (memoria compartida); S-M si se poda. **SM-1/SM-2:** nulo, con una prueba de que el resultado de la auditoría es idéntico. **Decisión de Alex:** solo para podar dependencias.

## 7. La evidencia de «configurados» se trunca sin avisar

**Problema (hecho).** Cierra la pregunta pendiente R7(b) del `deferred-work.md`. `app/agentes.py:82` fija `_LIMITE_COINCIDENCIAS = 3` y `:123` hace `sorted(encontrados)[:3]`. En esta carpeta `.claude` tiene 1031 archivos (el 49 % de lo recorrido, casi todo `skills`), y el reporte muestra 11 rutas de evidencia para Claude Code y 5 para BMAD, alfabéticas, sin «y N más». Quien mira la lista cree que son todas. No es un riesgo de seguridad, es un problema de honestidad del alcance (FR-20).

**Propuesta.** Guardar la cantidad real de coincidencias y mostrar «y 1028 más» junto a la evidencia, solo con el número. **Toca:** FR-31, FR-20, AD-18. **Esfuerzo:** S. **SM:** nulo. **Decisión de Alex:** no.

## 8. Ubicaciones sensibles: 10 filas para 2 funciones, y repetir la ejecución con una opción

**Problema (hecho).** Las 10 filas de «ubicación sensible sin activar» vienen de **dos detectores distintos**: 3 de `ubicaciones_usuario.py:80-83` (`~/.ssh`, `~/.aws`, `~/.npmrc`) y 7 de `instrucciones_fuera.py:39,55-58` (`~`, `~/Descargas`, `~/Desktop`, `~/Documentos`, `~/Documents`, `~/Downloads`, `~/Escritorio`). Con la opción apagada no se toca el disco (AD-9), así que AgentReach no sabe cuáles existen. Verifiqué solo existencia en esta máquina: **no existen** `~/.ssh`, `~/.aws`, `~/.npmrc`, `~/Descargas`, `~/Documentos` ni `~/Escritorio` (6 de 10). Cada fila repite «Si quieres... vuelve a ejecutar con `--incluir-ubicaciones-sensibles`». Para la persona son 10 pendientes; en realidad es una sola decisión. Y para tomarla tiene que **volver a ejecutar** toda la revisión (en esta carpeta, unos segundos; en otras, más) aunque ya contestó «sí» a la segunda pregunta de permiso (por eso se leyó `~/.claude/settings.json`).

**Propuesta.** (a) Agrupar en 2 filas: «Claves y credenciales de la carpeta personal (3 lugares)» y «Archivos de instrucciones sueltos en la carpeta personal (7 lugares)». (b) Evaluar una **tercera pregunta humana** al lado de las dos existentes: «¿Mirar también los nombres, tamaños y permisos de `~/.ssh`, `~/.aws`, `~/.npmrc`? Nunca se abre su contenido». Se contesta en la misma ejecución y conserva lo que dice AD-13 (nada de `--yes`; solo una persona en terminal).

**Toca:** FR-4, FR-30, FR-25; AD-9 (hoy solo la opción o `~/.agentreach/config.toml` encienden esto: la tercera pregunta lo cambia) y AD-13. **Esfuerzo:** S la agrupación; M la pregunta (+ pruebas de que sin terminal no se lee nada, y del canario). **SM-1:** nulo. **SM-2:** nulo (solo metadatos). **Riesgo no negociable:** un agente que simule la terminal podría contestar tres preguntas en vez de dos (FR-30/M1 ya lo marca como requisito previo al lanzamiento). **Decisión de Alex:** **sí**, es un cambio de AD-9; la agrupación (a) no la necesita.

## 9. «Qué cambió desde la última revisión»

**Problema (hecho para la necesidad).** Entre la corrida de ayer y la de hoy el único cambio fue +1 hallazgo `.env:10` (en 2 agentes) y +1 pack, +10 archivos; descubrirlo exigió un script. La propuesta de cambio de sprint ya fija «volver a escanear alrededor del 2026-12-11 y comparar con este reporte» como criterio de éxito: hoy esa comparación es manual. El reporte guarda cada HTML en `AgentReach-reportes` con los datos en JSON ya depurados por la compuerta, así que el insumo existe.

**Propuesta (hipótesis de diseño).** Al generar un reporte, buscar en `AgentReach-reportes` el último de la misma carpeta, leer su JSON y mostrar «Desde la revisión anterior: 1 hallazgo nuevo (`.env`, línea 10), 0 resueltos, 1 archivo no revisado nuevo». Solo claves de ruta, tipo y línea, nunca valores. Cuidados: la línea cambia si insertan una fila antes, así que la huella debería ser (ruta, tipo, proveedor, agente) con la línea como dato secundario; el HTML anterior es **dato no confiable** (alguien puede haberlo editado) y debe validarse contra el esquema de `docs/reporte-html/esquema-datos.schema.json`.

**Toca:** FR-20, FR-28, FR-3; AD-17 (esquema con `schema_version`), AD-19 (es lectura de la carpeta de reportes propios, fuera del proyecto: AD-13 solo cubre «reglas de agentes fuera del proyecto»; hay que decidir si esta lectura entra en el segundo permiso). **Esfuerzo:** M. **SM-1:** nulo. **SM-2:** nulo si solo se compara lo que ya está depurado; la prueba canario debe incluir un reporte anterior con una marca. **Decisión de Alex:** **sí**, por la lectura fuera de la carpeta revisada y por si conviene tener un modo «solo diferencias».

## 10. Claves privadas dentro del proyecto

**Problema (hecho, probado con nombres de archivo, sin leer nada).** `clase_de_archivo` devuelve `None` para `certs/server.pem`, `id_rsa`, `deploy.key`, `terraform.tfstate`, `prod.tfvars` y `keystore.jks` (ejecución de prueba hoy). Esos archivos no dan hallazgo y **tampoco** aparecen en «No se pudo revisar»: silencio total. `~/.ssh` y `~/.aws` se cubren (TH-2, TH-3) pero solo en la carpeta personal y con opt-in; una clave privada dentro del repo, que es lo que un agente sí puede leer, no. En el reporte de hoy **no** hay archivos de este tipo en el proyecto (revisé por nombre), así que el valor aquí es **hipotético**; la brecha de detección es real.

**Propuesta.** Reconocer por **nombre y extensión** (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `id_rsa*`, `*.tfstate`, `*.tfvars`) como TH-1 (o un TH nuevo) con nivel máximo Potencial (por nombre, sin fuente verificada: FR-7, AD-11), sin abrir el archivo. Es consistente con cómo se trata un `.env` demasiado grande («se reporta por nombre»: `archivos_repo.py:51-54`).

**Toca:** FR-4, FR-18 (catálogo y oráculo: casos nuevos, y quizá TH nuevo), FR-7. **Esfuerzo:** M (detector, catálogo ES/EN, casos del oráculo). **SM-1:** bajo (tope Potencial por diseño; el segundo cálculo no aplica). **SM-2:** nulo, solo nombres. **Decisión de Alex:** **sí**, amplía el alcance de FR-4 («lo que no coincide no se reporta»).

## 11. `.gitignore` como contexto de la acción de TH-1

**Problema (hipótesis).** El `.gitignore` de la carpeta revisada incluye `.env` (líneas 7 a 9: `.env`, `.env.local`, `.env.prod`); por tanto el riesgo de `.env` es sobre todo «lo lee el agente en este equipo», no «está subido al repositorio». La acción genérica («rótala si estuvo expuesta») no distingue los dos casos y la persona no sabe si debe rotar. Pero **ignorado no es lo mismo que no rastreado** (un archivo puede haberse subido antes o forzado), y la señal «rastreado por git» (GT-01) está diferida a «no determinado» en el MVP (pregunta 21 del PRD). Cualquier frase del tipo «no está en git» sería una afirmación sin fuente (SM-1/SM-C3).

**Propuesta.** Primero decidir y verificar; solo después implementar. Lectura posible: informar «`.gitignore` ignora este archivo (no prueba que no esté subido)» como contexto, sin tocar el nivel; la verificación real exigiría leer `.git/index`, que es binario. **Toca:** FR-22, FR-12; AD-6 (git como texto). **Esfuerzo:** L por la parte del índice. **SM-1:** alto si se afirma más de lo que se sabe; nulo si se limita a «dice el .gitignore». **Decisión de Alex:** **sí**; recomiendo no hacerlo hasta resolver la pregunta 21.

---

## Respuestas directas a las cuatro preguntas

**1. Cobertura: ¿qué pierde valor y cómo reducirlo?** De las 25 filas, solo 2 tienen valor de seguridad real hoy (`~/.claude/settings.json` por los hooks, y `.git` por el historial). Las 2 de packs son redundantes con `.git`; los 11 `.docx` están ahí por tamaño aunque ningún detector los abriría; las 10 de ubicaciones sensibles son una sola decisión (mejoras 2 y 8). Ganancia más segura: 25 a 5 filas sin cambiar una sola regla no negociable. Hay además silencios que **sí** esconden cobertura (xlsx, pdf, docx pequeños, claves privadas del proyecto; mejoras 2 y 10).

**2. Utilidad de la acción.** No alcanza: el único apoyo de priorización («Corregir primero») está vacío por diseño; 14 hallazgos son 7 acciones, y TH-14 no dice si es hook o MCP aunque el dato existe (mejoras 1 y 3).

**3. Precisión.** Los 10 Potencial se explican por **dos barreras apiladas** (reglas no modeladas más el tope por nombre de AD-11), y el reporte nombra solo la primera (mejora 5). La atribución de `.claude/settings*.json` a «ningún agente» quita señal a la pestaña que más la necesita (mejora 4). No propongo ninguna subida de nivel.

**4. Experiencia.** Seis recorridos del árbol (3,1 s solo en recorrer; mejora 6), tres pendientes de «no revisado» que se pueden resolver con una sola respuesta (mejora 8), evidencia truncada sin aviso (7) y ninguna comparación con la corrida anterior (9). El español/inglés y la `lang` ya están cubiertos por las historias 34 y 35.

## Qué verifiqué y cómo (para reproducir)

- Datos del reporte: script con `python -I` que lee el `<script type="application/json" id="data">` de los dos HTML y compara hallazgos y no revisados.
- Tamaños: `ls -l` sobre los `.docx` y `.git/objects/pack` de la carpeta revisada (solo metadatos).
- Tiempos: `recorrer()` ×6 y `leer_texto` de los 1716 archivos de clase TEXTO sobre la carpeta (sin leer `.env`), con el código del proyecto, en solo lectura.
- Detección: `clase_de_archivo` y `analizar` con nombres y valores de prueba inventados.
- Existencia de las ubicaciones de la carpeta personal: `[ -e ruta ]`, sin abrir nada.

## Lo que no pude comprobar

- El tiempo de una ejecución completa con todos los detectores y la CLI (no se puede automatizar: exige la confirmación humana de AD-13).
- El comportamiento en un proyecto con `node_modules` real (hipótesis de la mejora 6).
- Qué contiene realmente la línea 10 de `.env` (no se lee ningún `.env`; solo se sabe que el detector la marcó con proveedor «desconocido»).
- Si el reporte es representativo: sigue siendo una sola carpeta; confirmar con el segundo proyecto de prueba (pregunta 3 del research anterior).
