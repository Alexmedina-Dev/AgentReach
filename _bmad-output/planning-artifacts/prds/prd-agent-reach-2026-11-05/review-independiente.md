# Revisión independiente del PRD de AgentReach

**Veredicto:** el PRD tiene una tesis clara y unas reglas de seguridad bien fijadas, pero su corazón (cuándo un hallazgo es "comprobado") se contradice entre FR-5, FR-6 y FR-8, depende de decisiones aún abiertas (identidad del agente, cálculo de permisos en Windows) y se valida con una métrica (SM-1) que se puede cumplir sin que la herramienta sirva. Además no define qué tipos de hallazgo existen, así que un desarrollador no puede implementarlo sin preguntar.

Alcance de la revisión: `prd.md` (estado draft, actualizado 2026-11-06), contrastado con la rúbrica `prd-validation-checklist.md`, el brief, `.memlog.md` y `README.md`. No se asumió que lo afirmado en el PRD sea correcto. No se leyeron la arquitectura, la investigación ni el oráculo que el PRD cita (no estaban en el alcance encargado), por lo que lo que dependa de ellos queda señalado como "no verificable desde el PRD".

Valoración por dimensión de la rúbrica: decision-readiness, adecuada; substance over theater, fuerte; strategic coherence, adecuada; done-ness clarity, delgada; scope honesty, adecuada (mucho `[ASSUMPTION]`, pero hay huecos silenciosos); downstream usability, delgada; shape fit, adecuada (un solo UJ es razonable para una herramienta de un solo operador).

---

## CRÍTICO

### C-1. La lógica de niveles (FR-5, FR-6, FR-8) se contradice y deja casos sin resolver
- FR-5 define **comprobado** como: el archivo existe, el permiso efectivo lo permite y "ninguna regla del agente lo bloquea". FR-6 dice que un `deny` "no elimina ni rebaja el hallazgo". Si un `deny` bloquea, FR-5 impide "comprobado"; si no rebaja, FR-6 lo contradice. El PRD no dice qué nivel recibe un archivo legible por el sistema operativo y con `deny`. El `.memlog.md` (línea 22) dice que queda "potencial"; FR-6 dice que no se rebaja. Son lecturas incompatibles y un desarrollador elegiría al azar.
- FR-6 solo trata `deny`. Las reglas `ask` y `allow` explícitas no tienen efecto definido sobre el nivel ni sobre la nota. ¿Una regla `ask` es "bloqueo" para FR-5?
- FR-8 convierte en **potencial** un caso que AgentReach sí determinó ("hoy el agente no puede leerlo"), mientras FR-5 define potencial como "no se pudo determinar". "Potencial" pasa a significar dos cosas distintas (incierto vs. conocido-no-legible), y el usuario no puede distinguirlas en el reporte.
- FR-6 aclara que en opencode el `deny` de lectura no frena al shell, pero no dice nada de Claude Code (¿la regla `deny` de `Read` frena `cat` por Bash?). La nota obligatoria "protegido por política, no por barrera" se aplica igual en ambos casos sin base.
- *Arreglo:* añadir una tabla de decisión (existe / legible por el sistema operativo / regla `deny`, `ask`, `allow` o ninguna / sandbox presente) con el nivel y la nota resultantes por fila. Separar FR-8 con un motivo codificado distinto, por ejemplo `potencial:no-determinado` y `potencial:no-legible-hoy`. Hacer que FR-5 y FR-6 se refieran a esa tabla.

### C-2. "Comprobado" depende de decisiones y verificaciones que el PRD mismo deja abiertas
- FR-5 exige el permiso efectivo "a la identidad con que corre el agente". El PRD no dice cómo se obtiene esa identidad (usuario actual, elevado, otro usuario, servicio, proceso lanzado desde Visual Studio). §10 P7 ("cómo se lanza el agente y qué ve; sin investigar") y P5 (`ctypes` o `icacls`) siguen abiertas, y ambas condicionan FR-5. Es decir, el requisito central está redactado como decidido, pero su viabilidad no está validada.
- §9, primera fila: la prueba de permisos cubrió "2 casos simples" (memlog línea 66). Quedan sin probar grupos, herencia, ACE de denegación, propietario, atributos de enlace y rutas UNC o de red. Con ese respaldo, SM-1 (cero falsos "comprobado") se promete sobre una base casi sin evidencia.
- El `.memlog.md` (línea 66) indica que en el equipo de Alex **opencode no está instalado** y Visual Studio no se detectó. Los criterios de §7.3 (1) y FR-15 exigen que "la primera prueba" sea con opencode. Esa dependencia no aparece en §9 como riesgo ni como bloqueo.
- *Arreglo:* convertir P5 y P7 en decisiones previas al desarrollo (con responsable y fecha), o degradar explícitamente en FR-5 "comprobado" a "comprobado solo para la identidad del usuario actual" hasta validar. Añadir al §9 el riesgo "el entorno de prueba no tiene la plataforma principal instalada" con mitigación.

### C-3. SM-1 se puede cumplir sin que la herramienta sirva, y su "verdad de referencia" no está definida
- "Cero comprobado falsos" se satisface trivialmente si AgentReach nunca emite "comprobado". FR-7 ya fuerza máximo "potencial" para todo lo `[G⚑]`, y el propio `.memlog.md` (línea 55) dice que de 19 ítems solo 2 se verificaron por completo. La mayor parte de los tipos nunca podrá ser "comprobado". Hay contra-métrica de cobertura (SM-C2), pero no una métrica mínima de verdaderos "comprobado" ni un recall.
- No se define qué es un "comprobado falso". La verdad la dan el oráculo (hecho por el propio autor, con el mismo conocimiento que la herramienta) y el agente "testigo", que no es juez. Un comprobado "falso" por ACL contra un agente que sí lee por otra vía no está resuelto.
- "Cero" sobre un proyecto de prueba pequeño, diseñado por el mismo autor que las trampas, tiene poco poder estadístico. No se pide tamaño mínimo de muestra ni variedad (grupos, herencia, enlaces, otro usuario).
- SM-1 "valida FR-5 y FR-7", pero FR-6 y FR-8 (decisiones de nivel confirmadas por Alex) no tienen métrica. SM-3 "valida FR-10", pero FR-10 es sobre el formato de la evidencia, no sobre la comparación con el oráculo.
- *Arreglo:* definir "comprobado falso" operativamente (AgentReach dice comprobado y existe un método independiente y reproducible que demuestra lo contrario). Añadir una métrica pareja: mínimo N de hallazgos "comprobado" verdaderos en el proyecto de prueba, y una matriz de casos obligatorios (permitido, negado, grupo, herencia, otro usuario, `deny` de opencode, junction). Asignar FR-6 y FR-8 a SM-1.

### C-4. El PRD no define qué tipos de hallazgo existen ni qué escanea el MVP
- FR-4 dice que lo "no reconocido no se reporta", pero en ningún lugar se enumeran los tipos reconocidos (claves SSH, `.env`, tokens de proveedores, archivos de contexto, scripts de deploy, etc.). §3 define "Hallazgo" con ejemplos entre paréntesis y FR-11 habla de "un catálogo fijo" que vive fuera del PRD. Sin ese conjunto, no hay forma de saber cuándo el MVP está completo ni de calcular omisiones.
- Brecha con el brief y el README. El brief (Alcance del MVP, punto 1) incluye "archivos, repositorios, variables de entorno, credenciales, claves SSH, tokens, scripts, procesos y accesos de red alcanzables". El README añade "capacidades de alto impacto (scripts de deploy, migraciones)", "instrucciones sospechosas en archivos de contexto" y "symlinks, junctions, variables de entorno". El PRD deja fuera solo las instrucciones maliciosas (§7.2) y guarda silencio sobre procesos, red alcanzable, scripts de deploy y variables de entorno. FR-5 menciona variables de entorno como ejemplo de "hipótesis", pero ningún FR las busca. Hay recortes silenciosos del alcance heredado.
- El diferenciador (brecha entre lo declarado y lo alcanzable, "considerando permisos del SO, montajes, enlaces simbólicos, variables de entorno", según el brief) y SM-6 dependen de capacidades que ningún FR especifica.
- *Arreglo:* añadir una sección "Tipos de hallazgo del MVP" con tabla (tipo, cómo se reconoce, plataformas, nivel máximo alcanzable, entrada del catálogo FR-11). Añadir una lista explícita "heredado del brief/README y diferido" con procesos, red, scripts de deploy, variables de entorno, montajes y enlaces.

### C-5. FR-7 depende de un artefacto de pruebas, no de una propiedad del producto
- FR-7 habla de "un ítem del checklist del oráculo marcado `[G⚑]`". El oráculo es una auditoría de referencia para comparar (glosario), no parte de AgentReach. En ejecución, la herramienta necesita saber si el tipo de hallazgo tiene fuente primaria. Eso exige un atributo en el catálogo de tipos o en el adaptador ("fuente verificada: sí/no"), que el PRD no define.
- El efecto del riesgo mitigado "Rutas de herramientas de terceros sin fuente: máximo potencial" no tiene FR propio.
- *Arreglo:* reformular FR-7 como "cada tipo de hallazgo y regla de adaptador lleva un indicador de fuente verificada; sin ese indicador el nivel máximo es potencial". Referenciar el checklist solo como origen del dato.

---

## ALTO

### A-1. Enlaces simbólicos y junctions: hueco que puede romper FR-1/FR-4 (opt-in)
El README y el brief los presentan como parte del diferenciador. El PRD solo los nombra en §5 como algo "aislado". FR-4 permite leer **contenido** dentro del proyecto. Una junction o symlink del proyecto que apunte a `~/.ssh` haría que el escaneo de contenido entre en una ubicación sensible sin opt-in. Tampoco hay regla para ciclos.
*Arreglo:* FR nuevo: el escaneo no sigue enlaces fuera del proyecto para leer contenido; los reporta como hallazgo con destino y solo metadatos. Prueba: junction a una carpeta con canario, que no aparece en la salida.

### A-2. Mitigaciones de §9 sin requisito que las implemente
- "Cada reporte dice qué revisó y qué no pudo revisar" (riesgo de falsa seguridad): no hay FR ni criterio comprobable. Es probablemente el riesgo más relevante para un producto de seguridad y no tiene requisito.
- "Avisar cuando AgentReach no reconozca la configuración" y "Fijar la versión probada": sin FR, sin cómo se detecta la versión de la plataforma.
- "La definición del agente no siempre es visible: nivel baja a potencial": solo aparece como suposición en FR-9.
*Arreglo:* añadir FR de "Cobertura declarada" (el reporte lista rutas y tipos revisados, ubicaciones sensibles no activadas, configuraciones no reconocidas y versión de plataforma detectada) y asociarle una métrica.

### A-3. FR-14 y FR-15 no son comprobables ("adaptador completo")
FR-15 dice que el de opencode es "completo, con la misma calidad que el de Claude Code" y FR-14 que lee configuración "usuario, proyecto, local y gestionada" con "su precedencia". No hay lista de claves o reglas que cada adaptador debe extraer, ni rutas de la configuración de Claude Code en Windows (FR-15 sí da rutas), ni casos de prueba de precedencia. "Misma calidad" no tiene criterio.
*Arreglo:* anexar a cada FR una matriz (fuente de configuración, claves soportadas, precedencia, qué hace cuando falta o está mal formada) y definir "completo" como "cubre toda la matriz".

### A-4. FR-10 pide "archivo y línea", pero la tecnología elegida no los da
§5 apoya Python 3.12 por `tomllib` en la biblioteca estándar, y la configuración de las plataformas es JSON. Ni `json` ni `tomllib` devuelven números de línea. Para citar "regla con archivo y línea" hace falta un analizador propio o una dependencia. Esto choca con la decisión de mínima dependencia o con la verificabilidad de FR-10, y tampoco se aclara el manejo de JSONC (comentarios).
*Arreglo:* decidir y registrar (analizador propio con posiciones, o citar archivo y ruta de clave sin línea), y ajustar FR-10.

### A-5. "Ajeno a la tarea" es un campo degenerado (FR-9, consecuencia 1)
Se define como "fuera del directorio de trabajo del proyecto". FR-4 limita el contenido al proyecto y las ubicaciones sensibles son externas por definición. Resultado: todo lo del proyecto es "no ajeno" y todo lo externo es "ajeno", sin información adicional. Además AgentReach no conoce la tarea del agente (la visión misma es que "trabaja solo en `src/`" no limita nada). No queda claro de dónde sale el "directorio de trabajo".
*Arreglo:* definirlo o eliminarlo del MVP. Opción: un parámetro `--tarea-en <ruta>` y "ajeno" = fuera de esa ruta; sin parámetro, el campo vale "no determinado".

### A-6. Instalación global y por proyecto (FR-16) sin contenido ni consecuencias
No hay consecuencia comprobable, ni definición de qué contiene la política del proyecto (nombre y lugar son P8 abierta), ni precedencia global vs. proyecto. FR-4 dice que "nunca un archivo del proyecto" activa ubicaciones sensibles, así que la política del proyecto no puede contener eso, y no se dice qué sí. FR-16 menciona "compartible con el equipo" mientras §2.2 declara a los equipos "no usuarios" en v1. Está en el alcance del MVP (§7.1) sin definición.
*Arreglo:* o se define (esquema mínimo, precedencia, ejemplo) o se pasa a "fuera de alcance del MVP" y se deja solo la configuración global.

### A-7. "Auditar y advertir" no se distingue observablemente de "solo auditar" (FR-13)
FR-13 dice que "la advertencia la entrega el reporte, no un gancho". Entonces el reporte es el mismo mecanismo que "auditar". Todo el PRD promete "auditar y advertir" como capacidad máxima (FR-13, FR-15), pero no hay conducta de "advertir" que se pueda comprobar (¿códigos de salida? ¿aviso destacado? ¿severidad?). El README la muestra como un concepto aparte.
*Arreglo:* definir qué significa "advertir" (por ejemplo, código de salida distinto de cero ante "comprobado", resumen al inicio) o fusionar con "auditar".

### A-8. Criterios de salida del MVP (§7.3) no cubren las métricas ni son verificables
- §7.3 omite SM-4 (sin red, sin modificar), SM-5 (tercero añade adaptador), SM-6 (diferenciador) y el criterio de completitud de adaptadores. El README y el brief tratan SM-5 como criterio de éxito.
- El punto 1 ("se corren las pruebas") mide actividad, no resultado. El punto 5 ("Alex verifica que es correcto") es subjetivo, de una sola persona, que además es autora. El punto 2 duplica a SM-1.
- La lista está marcada como suposición de John, y la propia nota dice que Alex mencionó "agentes que chocan en paralelo" (significado "por aclarar" según el memlog, línea 59) que se resolvió como Fase 2 en FR-17; no queda en §7.3.
- *Arreglo:* mapear cada criterio de salida a un SM con umbral. Para el punto 5, registrar una lista de verificación firmada y los resultados de cada hallazgo en una tabla (coincide, extra confirmado, falso positivo u omisión) guardada como evidencia.

### A-9. Contradicciones con el README y el brief que el PRD no reconcilia
- **Adaptadores:** el brief fija "un adaptador de referencia: Claude Code" y deja el segundo como pregunta abierta. El PRD y el README ponen dos (Claude Code y opencode, ambos completos) y el orden de prueba empieza por opencode. El PRD no anota que se aparta del brief.
- **Niveles:** el README define comprobado como "evidencia de que el recurso es alcanzable" y su informe ilustrativo marca como POTENCIAL un archivo "legible por el usuario actual" por no haber verificado "con sus propios permisos". Con FR-5 (ACL de la identidad del agente) eso sería "comprobado". Aclarar la diferencia o actualizar el ejemplo.
- **MVP del README:** "Instrucciones sospechosas en archivos de contexto" aparece como característica del MVP; el PRD las excluye (§7.2). El README también promete "Funciona en Windows y POSIX" y el PRD limita el MVP a Windows.
- **Preguntas del brief descartadas sin registro:** el "puntaje AES" (brief P4) y los "repositorios de prueba de exposición conocida" no aparecen en el PRD; tampoco que se descartó el puntaje.
- **Sin red:** el README y el PRD hablan de "sin red *por defecto*", lo que implica un modo con red que no existe en ningún FR. O se elimina "por defecto" o se especifica el modo.
- *Arreglo:* sección corta "Cambios respecto al brief" y alinear el README en los puntos señalados.

---

## MEDIO

### M-1. Requisitos sin métrica, y métricas sin requisito
Sin métrica asociada: FR-4, FR-6, FR-8, FR-9, FR-11, FR-12, FR-14, FR-15, FR-16, FR-17 y el requisito transversal de determinismo (§5). Métricas con asignación débil: SM-3 -> FR-10 (ver C-3), SM-5 -> FR-13 (solo una consecuencia), SM-6 sin FR que la produzca. Ninguna métrica valida la explicación para novatos (FR-11), objetivo explícito de Alex.
*Arreglo:* añadir tabla de trazabilidad FR <-> SM y, donde falte métrica, una consecuencia de prueba.

### M-2. FR-11 no es comprobable tal cual
"Un novato puede entender el hallazgo sin buscar términos fuera del reporte" no tiene criterio. El catálogo vive en la carpeta del oráculo (artefacto de pruebas) y no se cita su tamaño ni su cobertura. No se dice en qué idioma salen los reportes ni si el catálogo se localiza (el producto es abierto y agnóstico, el contenido es en español).
*Arreglo:* criterio mecánico (cada sigla definida en la primera aparición, una entrada de catálogo por tipo, prueba de cobertura tipo -> entrada) más una prueba con lector. Declarar el idioma del MVP.

### M-3. Determinismo (§5) sin definición operativa
"La misma entrada produce el mismo reporte" no aclara qué es la entrada (¿incluye variables de entorno, hora, versión de la plataforma?), el orden de los hallazgos ni si el reporte lleva marca de tiempo o nombre de equipo.
*Arreglo:* definir entrada y orden canónico; prueba: dos ejecuciones consecutivas con diff vacío, excluyendo un campo de fecha identificado.

### M-4. Forma del reporte y de la CLI sin especificar
No se define formato de salida (texto, JSON), interfaz (comandos, flags, códigos de salida) ni el "formato común" del núcleo. Aparecen sin introducir "un flag de la línea de comandos" (FR-4) y `--redact-paths` (§10 P9). FR-1 dice que "el reporte sale por pantalla por defecto", pero la comparación con el oráculo (§8) y UJ-1 requieren conservar la salida; no se dice cómo se guarda fuera del proyecto. Cómo se elige plataforma y agente a auditar (autodetección o parámetro) tampoco está dicho, y FR-17 supone que se detectan varios.
*Arreglo:* sección "Interfaz mínima del MVP" con comandos, flags y formato de salida, aunque sea provisional.

### M-5. FR-3 y el contenido del reporte: las rutas también filtran
FR-3 permite ubicación exacta. Los nombres de archivo y rutas pueden contener datos sensibles (por ejemplo `token-cliente-X.txt`) y los reportes pueden terminar en CI, capturas o pegados en un chat. El propio PRD tiene `--redact-paths` como pregunta abierta (P9), mientras FR-9 y FR-10 exigen rutas exactas. Además, nombres de archivo con secuencias de escape de terminal pueden inyectar contenido al mostrarse "por pantalla". Es un riesgo propio de una herramienta que imprime nombres controlados por un tercero.
*Arreglo:* decidir P9 en el PRD y añadir "los nombres se sanean antes de mostrarse" como consecuencia de FR-3.

### M-6. FR-4 mezcla dos modos y roza el "No objetivo" de no abrir archivos
FR-4 lee contenido del proyecto, mientras §6 dice "No abre archivos para probar permisos". La distinción (leer contenido para reconocer, no para probar permisos) es válida pero hay que escribirla, y no se dice qué ocurre con archivos binarios, muy grandes o ilegibles para AgentReach, ni los límites de tiempo y tamaño (no hay requisitos de rendimiento). Un archivo que AgentReach no puede leer para reconocer pero que el agente sí podría leer queda como omisión silenciosa: relacionado con la falsa sensación de seguridad.
*Arreglo:* consecuencia: "archivos no leíbles por AgentReach se listan como no revisados"; añadir límites de tamaño, tiempo y comportamiento ante binarios.

### M-7. Terminología inconsistente respecto al glosario
- "Proyecto" (FR-1, FR-4), "repositorio" (FR-16, glosario de Proyecto de prueba), "proyecto auditado" (FR-1) y "entorno" (visión) se usan como equivalentes sin definir cuál es el objeto de la auditoría. Dos de esos términos tienen efecto técnico distinto (carpeta frente a repositorio git frente a máquina con ubicaciones sensibles).
- "Agente" vs "plataforma": FR-17 dice "más de un agente o plataforma", UJ-1 dice "usar Claude Code y opencode (y su agente Dev-Alex)", FR-9 (5) separa "plataforma y agente". El glosario define el agente como programa con instrucciones definidas por el usuario, pero cuando el usuario usa Claude Code sin agente propio, ¿qué se reporta como "agente"?
- "Postura del agente" (glosario: lo que declara la plataforma para el agente) aparece en FR-5 como "regla del agente", y en FR-6 como "política del agente". Unificar.
- "Evidencia" en el glosario excluye explícitamente nada, pero en FR-10 aparece "hechos de su evidencia" distintos de "comando de verificación". Consistencia mínima.
*Arreglo:* ajustar el glosario: añadir "Proyecto auditado" y "Directorio de trabajo", y reemplazar en FR los sinónimos.

### M-8. Supuestos que deberían ser decisiones o riesgos
- FR-6 etiqueta "verificado para opencode 2.x" y a la vez lo marca como `[ASSUMPTION]`; el memlog (línea 20) lo daba como fuente de terceros sin verificar y opencode no está instalado en el equipo (línea 66). "Verificado" no debe usarse si fue por lectura de documentación.
- FR-5 (criterios de "comprobado"): aprobado como "enfoque" por Alex, pero la implementación (identidad, ACL) es no validada; es un riesgo, no un hecho. No lleva `[ASSUMPTION]`.
- §5 "los archivos de configuración de las plataformas pueden contener valores sensibles; el lector descarta los valores" es `[ASSUMPTION]` pero es una regla de seguridad con consecuencias: debe ser FR con prueba canario (tokens MCP).
- FR-1 (el reporte no se escribe dentro del proyecto): suposición que cambia comportamiento observable; decidir.
- §2.2 (agentes que no corren en el equipo, como ChatGPT en navegador, no se auditan): lo dicho en el memlog (línea 47) es que se tratan a escala después, lo que contradice "no hay nada que auditar".
*Arreglo:* promover a decisiones las que Alex ya aprobó y mover a §9 las que dependen de validación.

### M-9. Riesgos que faltan en §9
- **Sesgo del oráculo y del proyecto de prueba:** quien crea trampas, checklist, oráculo y herramienta es la misma persona; las pruebas pueden sobreajustarse. Mitigación: segundo proyecto de prueba creado por otro (o por un agente independiente) sin ver el código.
- **El reporte es un dato sensible en sí mismo** (mapa de dónde están los secretos). Mitigación: ver M-5.
- **Entorno de pruebas incompleto:** opencode no instalado, Visual Studio no detectado (ver C-2).
- **Cadena de suministro de la propia herramienta:** `uv tool install` y dependencias de una herramienta de seguridad con acceso de lectura al entorno. Mitigación: pocas dependencias, versiones fijadas, firma.
- **Rutas de red o UNC en Windows:** leer metadatos de un recurso compartido es acceso a red y viola FR-2.
- **Interpretación errónea de "potencial":** un usuario puede leer "potencial" como "riesgo menor", y FR-8 usa "potencial" para archivos que hoy no se pueden leer.
- **Ejecución en entornos distintos del probado (WSL2, contenedores):** Windows nativo se prueba, pero Claude Code ofrece sandbox en WSL2; ¿qué hace AgentReach si detecta WSL?
- **Persona única:** todo (verificación, criterio final, fuente de decisiones) depende de Alex.

### M-10. Experiencia de usuario: un solo UJ no cubre los caminos que el PRD exige
UJ-1 tiene protagonista (Alex) y un caso límite, pero no cubre: activar ubicaciones sensibles (opt-in), dos agentes sobre el mismo proyecto (FR-17), la plataforma sin sandbox de Windows (FR-14), el autor de un adaptador (SM-5) ni el reporte "vacío" (riesgo de falsa seguridad). Para una herramienta de un solo operador no hace falta uno por FR, pero sí por cada camino que tiene métrica.
*Arreglo:* añadir UJ-2 (opt-in y multiagente) y UJ-3 (tercero con adaptador) breves.

---

## BAJO

- **B-1. §10 P1** ("Fuera de alcance y riesgos: revisar con Alex §7.2 y §9") no es una pregunta abierta sino una tarea. P10 repite SM-6 (`[ASSUMPTION]`). Reducir duplicados.
- **B-2. §5, Python 3.12:** el argumento "recibe soporte más tiempo que 3.11" no justifica 3.12 frente a 3.13; el motivo real (`tomllib` está en 3.11+) no distingue 3.12. Registrar la razón efectiva o fijar un criterio (por ejemplo, la versión que `uv` instala por defecto).
- **B-3. FR-10 mezcla requisito y datos de investigación.** La lista de comandos no seguros (`gh auth status`, `dotnet user-secrets list`, `az account get-access-token`, `aws configure list`) pertenece al catálogo o a un anexo, no a las consecuencias de un FR. Falta además una consecuencia para rutas con espacios o caracteres especiales al construir el comando sugerido (escape por plataforma).
- **B-4. FR-2:** "una prueba con los sockets bloqueados termina con el mismo resultado" no define cómo se bloquea (firewall, namespace, parche de `socket`) ni cubre `subprocess` (como `icacls`) y resolución de nombres.
- **B-5. FR-1:** "marcas de modificación" ignora la fecha de último acceso, que algunos sistemas actualizan al leer; indicar qué marcas se comparan.
- **B-6. UJ-1** dice "Windows 11 nativo, va a usar Claude Code y opencode (y su agente Dev-Alex)" y lo marca como `[ASSUMPTION]` inferido. Dev-Alex vive fuera del proyecto (memlog línea 47); aclarar si se audita como agente definido en `~/.claude/agents` o como caso aparte.
- **B-7. Referencias a documentos externos** (§0): arquitectura, investigación y oráculo se citan como insumos "no duplicados", pero FR-7, FR-10 y FR-11 dependen de su contenido. Si cambian, el PRD queda inconsistente sin aviso. Añadir versión o fecha de los insumos.
- **B-8. Índice de supuestos (§11):** el viaje de ida y vuelta es correcto (todas las etiquetas del texto están indexadas y viceversa); el índice de §5 agrupa tres supuestos en una línea y conviene separarlos para que las épicas los referencien. Los IDs FR-1 a FR-17, SM-1 a SM-6 y SM-C1 a SM-C2 son contiguos y únicos, y las referencias cruzadas resuelven. No hay UJ huérfanos.
- **B-9. Estilo:** el encabezado §0 "Propósito" incluye el ámbito y la lista de insumos; el glosario figura como §3 pero "Visión" y "Usuario objetivo" aparecen antes de definir términos usados en ellos (alcanzable, hallazgo). Ordenar o enlazar.

---

## Notas mecánicas

- **Glosario:** ver M-7. Términos del glosario bien usados: "Hallazgo", "Núcleo", "Adaptador", "Oráculo", "Proyecto de prueba", "Nivel de confianza". Términos usados sin definición: "Directorio de trabajo", "Proyecto auditado", "Capacidad del adaptador" (definida solo dentro de Adaptador), "testigo" (definida solo en §8).
- **IDs:** contiguos, sin duplicados; SM-C1/SM-C2 como contra-métricas bien enlazadas con SM-1 y SM-3.
- **Referencias cruzadas:** las de §3 (FR-9, FR-5), §4.2 (§10) y §0 (§3, §11) resuelven. Referencia rota de contenido: FR-7 apunta al "checklist del oráculo", que no está en el PRD y no se cita con ruta.
- **Densidad de pendientes:** 14 etiquetas `[ASSUMPTION]` en el texto, 2 `[NOTE FOR PM]`, 10 preguntas abiertas. Para un PRD interno de fase de pruebas es aceptable; para pasar a épicas es un bloqueo en los puntos C-1, C-2 y C-4.
- **Secciones requeridas:** presentes (visión, usuario, glosario, FR, no objetivos, alcance, métricas, riesgos, preguntas, supuestos). Faltan "Tipos de hallazgo" (C-4), "Interfaz mínima" (M-4) y "Trazabilidad FR-SM" (M-1).

## Prioridad sugerida antes de pasar a épicas
1. Resolver la tabla de niveles (C-1) y decidir P5 y P7 (C-2).
2. Definir el catálogo de tipos de hallazgo y el alcance heredado del brief y del README (C-4, C-5).
3. Reescribir SM-1 con definición operativa, matriz de casos y métrica complementaria (C-3).
4. Añadir los FR de cobertura declarada y de enlaces/junctions (A-1, A-2).
5. Alinear README y brief con el PRD (A-9).
