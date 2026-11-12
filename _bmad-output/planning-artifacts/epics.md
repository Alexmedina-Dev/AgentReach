---
status: draft
stepsCompleted: [1, 2, 3]
modo: retroactivo
created: 2026-11-11
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md
  - _bmad-output/planning-artifacts/architecture/arquitectura-borrador.md
  - _bmad-output/planning-artifacts/historias-mvp.md
  - _bmad-output/implementation-artifacts/spec-historia-*.md
  - _bmad-output/planning-artifacts/mejoras-posteriores.md
  - _bmad-output/implementation-artifacts/deferred-work.md
  - docs/oraculo-confirmacion/confirmacion.md
  - docs/reporte-terminal/diseno.md
  - docs/presentacion-terminal/diseno.md
  - docs/boceto-reporte/
---

# agent-reach - Desglose de épicas

## Resumen

Este documento agrupa **retroactivamente** las historias del MVP de AgentReach (1 a 26, con sus variantes `b` y `c`) en épicas, y las conecta con los requisitos del PRD v0.2 (2026-11-11). **No reabre ni rehace nada**: las historias conservan su número, su spec y su estado. Sirve para (a) ver qué requisitos no tienen historia, (b) generar el `sprint-status` y (c) la revisión de preparación para implementar.

**Nota sobre los insumos:** la arquitectura (`arquitectura-borrador.md`) sigue en `status: draft` y está **desfasada** respecto a decisiones posteriores (ver «Requisitos adicionales»). No existe un contrato de UX formal (`DESIGN.md` y `EXPERIENCE.md`): los diseños de `docs/` hacen de contrato de UX. Los identificadores `FR-n` se conservan tal cual del PRD (no se renumeran).

## Inventario de requisitos

### Requisitos funcionales

**4.1 Auditoría de solo lectura**
- **FR-1:** AgentReach no modifica archivos, configuración ni variables del entorno que audita. No ejecuta ningún programa externo (ni `git`, ni `icacls`). Solo escribe el archivo de `--salida` y la carpeta `AgentReach-reportes` fuera de la carpeta revisada, y solo abre el navegador con permiso (Historia 21).
- **FR-2:** Sin red, sin excepciones y sin modo «con red». Prueba automática que bloquea sockets.
- **FR-3:** Ningún reporte, registro ni error contiene el valor de un secreto; los nombres y rutas se limpian de caracteres de control.

**4.2 Reconocimiento de hallazgos**
- **FR-4:** Reconocer por nombre, patrón o contenido (conservando solo tipo y ubicación). Ubicaciones sensibles opt-in y solo metadatos. Plantillas y valores de relleno no se reportan.

**4.3 Alcanzabilidad y nivel de confianza**
- **FR-5:** Asignar nivel (comprobado / potencial / hipótesis) con la tabla de decisión; permiso efectivo sin abrir el archivo, solo para el usuario que ejecuta; los permisos heredados no bajan el nivel.
- **FR-6:** Una regla `deny` o `ask` no borra el hallazgo: queda en potencial con la nota «política, no barrera». Las reglas del agente son contexto.
- **FR-7:** Sin fuente verificada, máximo potencial (indicador por tipo y por regla de adaptador).
- **FR-8:** Archivo que existe pero el agente no puede leer: potencial, nunca «no alcanzable».

**4.4 Hallazgo y reporte**
- **FR-9:** Ocho campos por hallazgo (incluye «ajeno a la tarea» por README y `--tarea`).
- **FR-10:** Evidencia reproducible: ruta, regla con archivo y línea («línea no determinada» si no se puede), comando de verificación seguro. Localizador de línea propio.
- **FR-11:** Explicación en lenguaje llano desde un catálogo fijo, bilingüe español/inglés. *Deuda registrada: el nombre de Copilot (FR-31) va solo en español.*
- **FR-12:** «Qué hacer» recomienda sin ejecutar (incluye la política de organización de opencode para `*.env`).

**4.5 Plataformas y adaptadores**
- **FR-13:** Adaptador agnóstico; «advertir» = reporte ordenado por nivel + código de salida (0, 1, 2, 3 y `--estricto`).
- **FR-14:** Adaptador de Claude Code (usuario, proyecto, local, gestionada; sin sandbox en Windows nativo).
- **FR-15:** Adaptador de opencode completo, 1.x y 2.x; lee también la configuración del usuario y la gestionada, sin valores del bloque de entorno.
- **FR-16:** Instalación global; política propia por proyecto después del MVP.
- **FR-17:** Un reporte (o sección) por agente; nivel esperado por agente.

**4.6 Catálogo, enlaces y cobertura**
- **FR-18:** Catálogo de tipos de hallazgo TH-1 a TH-22, con fuente verificada, explicación fija y nivel máximo por tipo.
- **FR-19:** No seguir enlaces que salen del proyecto: se reporta el enlace y su destino, nunca lo que hay detrás.
- **FR-20:** Cobertura declarada: qué se revisó y qué no se pudo revisar; un reporte vacío no se lee como «seguro».
- **FR-21:** Sección fija de límites (lo que AgentReach no detecta), en español e inglés.
- **FR-22:** Lectura de git como texto, sin ejecutar git; configuración no interpretable → TH-20.

**4.7 Honestidad del propio reporte**
- **FR-23:** Autocomprobación antes de imprimir: corrige hacia abajo o declara, nunca imprime algo que no pasó la revisión.
- **FR-24:** Verificación independiente: segundo cálculo del permiso, oráculo confirmado desde fuente primaria por quien no ve el código, y prueba de refutación.
- **FR-25:** «No se pudo revisar» con motivo de lista cerrada y «cómo resolverlo» en dos idiomas.
- **FR-26:** Límites duros comunes de lectura (`leer_seguro`): no sigue enlaces, solo archivos regulares, 5 MB, UTF-8 estricto, profundidad máxima; topes de 20000 hallazgos y 20 MB, código 3.

**4.8 Reporte de terminal y HTML**
- **FR-27:** Reporte legible en la terminal de Windows (ancho, color, codificación, idioma, tono, banner, `doctor`, tema, por agente).
- **FR-28:** Reporte HTML estático, sin red ni scripts externos, con vista Recorrido, ES/EN, por agente.
- **FR-29:** Detección de agentes por lógica (presencia de sus archivos de configuración); nunca se le pide al usuario elegirlos.

**4.9 Uso diario y honestidad del alcance (añadidos en el PRD v0.2)**
- **FR-30:** Permiso de lectura dado por una persona y su endurecimiento (Historias 22 y 23). **Requisito previo al lanzamiento público (M1):** que un agente no pueda simular la terminal; leer la confirmación de `CONIN$` o `/dev/tty` y registrar el modo de ejecución en el reporte.
- **FR-31:** Reconocer un agente (catálogo de 22) no es analizar su alcance (solo Claude Code y opencode); el reporte lo declara. GitHub Copilot es un solo agente cuando la señal es compartida.
- **FR-32:** El reporte dice por qué un nivel es «no determinado»: archivo y clave, sin valores.

### Requisitos no funcionales

- **NFR-1 (Solo lectura):** el árbol auditado queda idéntico tras la ejecución (FR-1).
- **NFR-2 (Sin red):** ninguna conexión, comprobada con una prueba que bloquea sockets (FR-2).
- **NFR-3 (Sin valores de secretos):** prueba canario, sin campo capaz de contener un valor (FR-3).
- **NFR-4 (Bilingüe):** producto en español e inglés; cada tipo del catálogo con explicación en ambos idiomas (FR-11).
- **NFR-5 (Determinismo):** la misma entrada produce el mismo reporte; la fecha entra por un reloj inyectado.
- **NFR-6 (Sistemas):** probado en Windows 11 nativo; lo propio de cada sistema aislado para extender a Linux y macOS.
- **NFR-7 (Tecnología):** Python 3.12+, CLI con `uv`, **solo biblioteca estándar** (sin dependencias en ejecución).
- **NFR-8 (Configuraciones de plataformas):** el lector descarta los valores sensibles (tokens MCP, variables).
- **NFR-9 (Sin ejecutar programas):** ni `git` ni `icacls` ni otro; prueba que reemplaza `subprocess` y familias por funciones que fallan.
- **NFR-10 (Límites de lectura):** lectura solo con `leer_seguro` y tiempo acotado ante archivos hostiles.
- **NFR-11 (Conducta de producto):** nunca decir «seguro»; sin hallazgos dice «no se encontró nada en lo que pudo revisar».

### Requisitos adicionales (arquitectura y métricas)

- **AD-1:** Núcleo hexagonal (puertos y adaptadores) con el modelo de hallazgo como contrato; `core` no importa `adapters`, `infra` ni `reporting`.
- **AD-2:** Adaptadores: el de referencia (Claude Code) vive en el árbol; el borrador propone además *entry points* de Python para terceros y un kit de conformidad. **Desfase verificado el 2026-11-11:** el kit existe (`adapters/conformance`); los *entry points* **no existen** (ni en `pyproject.toml` ni en `src/`). Hoy un tercero solo podría añadir un adaptador tocando el árbol del paquete, lo que incumple SM-5.
- **AD-3:** «Solo lectura» impuesta por el puerto `ReadOnlyFs` y la prueba de árbol intacto.
- **AD-4:** «Sin red» por ausencia estructural más prueba de sockets.
- **AD-5:** Permisos del SO con `ctypes` (`AccessCheck`), sin abrir archivos; segundo cálculo independiente (FR-24).
- **AD-6:** Git leído como texto con lector propio; ejecutar git con defensas es fase 2.
- **AD-7:** `dataclasses` congeladas, sin Pydantic. **Desfase:** el borrador dice Python 3.11; el PRD y `pyproject.toml` dicen **3.12**.
- **AD-8:** Formatos de reporte. **Desfase:** el borrador propone JSON canónico + Markdown + terminal y pospone SARIF; lo construido es terminal + **HTML** (+ JSON y CSV exportados desde el HTML).
- **AD-9:** Ubicaciones sensibles opt-in, solo metadatos; encenderlas solo por configuración global o flag.
- **AD-10:** Puerto `Narrator` vacío; sin modelo de lenguaje en el MVP.
- **Métricas que las épicas deben poder demostrar:** SM-1 (cero «comprobado» falsos), SM-2 (cero valores de secretos), SM-3, SM-4, SM-5 (un tercero añade un adaptador con documentación), SM-6 (diferenciador), SM-7 (todos los comprobados esperados, 67 casos) y SM-8 (determinabilidad en configuraciones reales).

### Requisitos de diseño de UX

*(Extraídos de FR-27, FR-28 y de `docs/reporte-terminal/diseno.md`, `docs/presentacion-terminal/diseno.md` y `docs/boceto-reporte/`.)*

- **UX-DR1:** Terminal con ancho entre 60 y 100 columnas: ninguna línea pasa del ancho menos uno ni parte una palabra (salvo una ruta indivisible). **Aplica a todo lo que se imprime**, no solo al cuerpo del reporte: los textos de bienvenida, las preguntas y los avisos hoy no pasan por el ajuste (Historia 30).
- **UX-DR2:** Color con tema `claro|oscuro|auto`; paleta de marca exacta (AGENT `#EAF4F2`, REACH `#3DF5D0`, ámbar, violeta, azul); el color nunca es lo único: siempre símbolo y palabra de nivel; sin `ESC` si no hay color. **Adaptación automática (decidida el 2026-11-11 tras verlo fallar en Orca):** nada puede quedar ilegible aunque no se sepa si el fondo es claro u oscuro; detección por capas y colores neutros como último recurso (Historia 29).
- **UX-DR3:** Codificación segura (cp437, cp1252, UTF-8) sin `UnicodeEncodeError`; símbolos con respaldo ASCII; **sin emojis**.
- **UX-DR4:** Idioma automático por configuración regional (`--idioma`, `AGENTREACH_IDIOMA`) y tono «tú» por defecto o formal (`--tono`, `AGENTREACH_TONO`).
- **UX-DR5:** Banner de marca en tres tamaños (grande sin argumentos, mediano en `doctor` y al revisar, mínimo en el reporte), solo en terminal interactiva, nunca con redirección, `NO_COLOR`, `--no-banner` ni `--json`.
- **UX-DR6:** Comando `agentreach doctor` con 7 comprobaciones de solo lectura y la frase «AgentReach no modifica nada ni ejecuta ningún programa».
- **UX-DR7:** Caracteres peligrosos en un nombre (control, inversión, ancho cero) se muestran **escritos** (`‮`) con una nota, no se borran en silencio.
- **UX-DR8:** Una sola sección «No se pudo revisar» con dos partes: A (lo concreto, agrupado por motivo, con «cómo resolverlo» una vez) y B (límites fijos).
- **UX-DR9:** Terminal con resumen corto por nivel y los 3 hallazgos más urgentes; el listado completo solo con `--detalle`; sin códigos `TH-n` ni identificadores de motivo sin `--detalle`.
- **UX-DR10:** Flujo de uso diario: carpeta actual, permiso `s/n`, resumen, indicación de dónde está el reporte visual y pregunta `s/n` de abrirlo en el navegador.
- **UX-DR11:** HTML con Paleta A (rojo = comprobado, ámbar = potencial, gris = hipótesis, violeta = no se pudo revisar), cada nivel con icono y forma; tabla, orden, filtros, exportar e imprimir; ES/EN; sin red ni scripts externos.
- **UX-DR12:** Vista Recorrido (ES) / Route (EN); con más de 60 hallazgos no se dibuja el grafo detallado y se muestra un recorrido resumido no seleccionable.
- **UX-DR13:** El selector del reporte solo incluye agentes con adaptador; los reconocidos pero no analizados se listan como «configurados» con su aviso (FR-31).
- **UX-DR14:** Rutas relativas a la carpeta revisada (la absoluta solo en el encabezado); `--salida ARCHIVO` en UTF-8, rechazada dentro del proyecto auditado.
- **UX-DR15:** Lenguaje llano en todo el reporte (decidido por Alex el 2026-11-11): cada término técnico que aparece trae su «qué es» y su «qué significa para ti», sin jerga interna; la terminal lo dice en una frase y el HTML y el README lo desarrollan, desde un único catálogo (Historia 32).

### Mapa de cobertura de FR

Cada requisito tiene una épica **principal**; los que tocan más de una lo indican. «Hecho» = construido y con pruebas; «pendiente» = aún sin historia.

| FR | Épica | Qué cubre | Estado |
|---|---|---|---|
| FR-1 | E5 | Solo lectura y excepciones acotadas (escritura de reportes, abrir el navegador) | Hecho (14, 21, 22) |
| FR-2 | E5 | Sin red, prueba de sockets | Hecho (14) |
| FR-3 | E5 | Sin valores de secretos, prueba canario | Hecho (14); también 1, 4 |
| FR-4 | E1 | Reconocer por nombre, patrón o contenido; ubicaciones sensibles opt-in | Hecho (4, 5) |
| FR-5 | E3 | Nivel de confianza y su tabla de decisión | Hecho (3, 11, 18) |
| FR-6 | E3 | `deny` y `ask` no borran el hallazgo | Hecho (9, 10, 11) |
| FR-7 | E3 | Sin fuente verificada, máximo potencial; tope por nombre | Hecho (11, 27) |
| FR-8 | E3 | Archivo existente pero no legible | Hecho (11) |
| FR-9 | E4 | Ocho campos por hallazgo; «ajeno a la tarea» es de E3 | Hecho (13; 12) |
| FR-10 | E4 | Evidencia reproducible, archivo y línea | Hecho (13); localizador previo |
| FR-11 | E4 | Explicación llana y bilingüe | Hecho, **con deuda** (nombre de Copilot solo en español → E7) |
| FR-12 | E4 | «Qué hacer» sin ejecutar | Hecho (13) |
| FR-13 | E3 | Adaptador agnóstico; «advertir» y códigos de salida | Hecho (9, 10, 13) |
| FR-14 | E3 | Adaptador de Claude Code | Hecho (9, 11b, 11c) |
| FR-15 | E3 | Adaptador de opencode 1.x y 2.x | Hecho (10, 10b) |
| FR-16 | E1 | Configuración global; política por proyecto posterior | Hecho (5) |
| FR-17 | E4 | Un reporte por agente | Hecho (13, 13c) |
| FR-18 | E2 | Catálogo TH-1 a TH-22 | Hecho (1, 4 a 8, 16, 17) |
| FR-19 | E1 | No seguir enlaces que salen del proyecto | Hecho (2) |
| FR-20 | E4 | Cobertura declarada | Hecho (13) |
| FR-21 | E4 | Límites declarados | Hecho (13) |
| FR-22 | E2 | Lectura de git sin ejecutar git | Hecho (7) |
| FR-23 | E4 | Autocomprobación antes de imprimir | Hecho (13) |
| FR-24 | E5 | Verificación independiente y oráculo | **Parcial**: 15 construida, no cerrada |
| FR-25 | E1 | «No se pudo revisar» con motivo y salida | Hecho (4b) |
| FR-26 | E1 | Límites duros de lectura | Hecho (4b) |
| FR-27 | E4 y E5 | Reporte legible en terminal | Hecho (13b, 13c) **con 2 defectos**: banner en fondo claro → Historia 29 (E4); ancho de los textos de bienvenida y preguntas → Historia 30 (E5) |
| FR-28 | E4 | Reporte HTML estático | Hecho (19, 20, 21) |
| FR-29 | E6 | Detección de agentes por lógica | Hecho (24) |
| FR-30 | E5 y **E7** | Permiso de lectura de una persona, dos niveles | Hecho (22, 23, 27 las letras, 28). **Pendiente: M1** (E7) |
| FR-31 | E6 | Reconocer no es analizar | Hecho (24, 26) |
| FR-32 | E6 | Por qué un nivel es «no determinado» | Hecho (25, 28) |

**Sin cobertura (todo en E7):** M1 de FR-30; deuda bilingüe de FR-11; métrica SM-8; SM-5 (guía y registro de adaptadores de terceros); oráculo en la suite por defecto; decisión de `--redact-paths`; preparación del repositorio público.

## Lista de épicas

*Aprobada por Alex el 2026-11-11. Organizadas por valor para el usuario; ninguna épica necesita una posterior para funcionar. Las historias 1 a 28 son retroactivas: conservan su número y su spec en `implementation-artifacts/`.*

### Épica 1: Ver qué secretos quedan a la vista
El usuario ejecuta `agentreach` sobre una carpeta y ve credenciales, claves y ubicaciones sensibles, sin valores de secretos y con lo no revisado declarado.
**Historias:** 1, 2, 4, 4b, 5, 5b, 6 · **FR:** FR-4, FR-16, FR-19, FR-25, FR-26 · **Estado:** terminada.

### Épica 2: Detectar lo que se ejecuta solo o engaña al agente
El usuario sabe si git, los archivos de contexto o el texto invisible pueden hacer que algo se ejecute, sin que AgentReach ejecute nada.
**Historias:** 7, 8, 16 · **FR:** FR-18, FR-22 · **Estado:** terminada.

### Épica 3: Saber con cuánta certeza llega el agente
Cada hallazgo trae su nivel (comprobado, potencial o hipótesis) con permisos de Windows, reglas de Claude Code y opencode, «ajeno a la tarea» y el tope por nombre.
**Historias:** 3, 9, 10, 10b, 11, 11b, 11c, 12, 17, 18, 27 · **FR:** FR-5, FR-6, FR-7, FR-8, FR-13, FR-14, FR-15 · **Estado:** terminada. *(La 27 tiene además la parte de las letras `(S/N)`, que es de FR-30.)*

### Épica 4: Entender el resultado de un vistazo
El usuario lee el reporte en la terminal y en el navegador, en español o inglés, con color accesible, `doctor` y un flujo diario simple, en **cualquier** terminal.
**Historias:** 13, 13b, 13c, 19, 20, 21 (terminadas) · **29 (nueva)** · **FR:** FR-9 a FR-12, FR-17, FR-20, FR-21, FR-23, FR-27, FR-28 · **Estado:** terminada con **1 corrección nueva** y verificaciones manuales cerradas por Alex el 2026-11-11 (19, 20, 21; la 13b y la 13c con los defectos hallados en Orca).

### Épica 5: Confiar en que la herramienta no daña ni miente
Pruebas bloqueantes de solo lectura, sin red y sin secretos; oráculo de 67 casos; permiso de lectura dado solo por una persona, en dos niveles.
**Historias:** 14, 15, 22, 23, 28 (terminadas, salvo la 15) · **30 (nueva)** · **FR:** FR-1, FR-2, FR-3, FR-24, FR-30 (permiso) · **Estado:** terminada **salvo la 15** (construida, no cerrada: 22 casos sin verificar en fuente primaria, de ellos 6 esperados como comprobado, y tus verificaciones manuales).

### Épica 6: Saber qué agentes hay y por qué algo no se determinó
El usuario ve los agentes configurados, qué analiza AgentReach y qué solo reconoce, y el archivo y la clave que impiden un nivel.
**Historias:** 24, 25, 26 · **FR:** FR-29, FR-31, FR-32 · **Estado:** terminada.

#### Story 6.5 (Historia 33): «Cómo leer este reporte» va primero y siempre visible en el HTML *(terminada 2026-11-11; falta tu comprobación en el navegador)*
Como persona que termina la revisión en la terminal y abre el reporte HTML, quiero ver **antes del reporte**, siempre, qué significa cada nivel y qué es un camino de alcance, para entender cada enlace y gestionar bien lo que veo. FR-11, FR-28, UX-DR15. *Origen: Alex propuso que el HTML lleve siempre, antes del reporte, la descripción de cada nivel (como el README) porque hoy el HTML solo trae una leyenda de una línea dentro del reporte y los caminos no se explican en ningún lugar.*

**Criterios de aceptación:**

**Given** cualquier reporte HTML (con o sin hallazgos)
**When** se abre
**Then** la sección «Cómo leer este reporte» es lo **primero**, abierta por defecto (se puede plegar) y sale en español (tú y usted según el tono) e inglés.

**Given** la sección
**When** se lee
**Then** define los tres niveles con su significado completo (qué se comprobó y qué no): **Comprobado** (tres cosas ciertas a la vez: el archivo existe, los permisos del sistema dejan leerlo a quien ejecuta el agente y ninguna regla del agente lo bloquea; se comprueba por permisos, sin abrir el archivo), **Potencial** (existe y el agente podría llegar, pero una de las tres cosas no se pudo confirmar; por ejemplo una regla del agente que lo prohíbe pero que no es una barrera real del sistema) e **Hipótesis** (una señal débil o indirecta que debes comprobar a mano).

**Given** la sección
**When** se lee
**Then** explica el **camino de alcance** (Agente → Dónde → Qué hay → Efecto posible) y qué significa la línea continua (AgentReach lo comprobó) y la discontinua (no lo comprobó); y los demás términos del catálogo de la Historia 32 que aparezcan.

**Given** el texto de la sección
**When** se redacta
**Then** nunca dice «seguro» ni «sin riesgo» (no «lo seguro que es», sino «con qué firmeza lo sabemos»), y usa «Comprobado» en español y «Verified» en inglés.

**Given** la vista Imprimir
**When** se imprime
**Then** la sección se incluye abierta.

**And** todos los textos propios del HTML siguen el tono elegido (hoy mezclan «usted»), y una prueba compara las definiciones con el catálogo y con el README.

**Pendiente de decidir (con Alex):** el nombre inglés del camino, porque «path» en inglés ya significa ruta de archivo (propuesta: «Reach route»; la vista «Route» pasaría a «Route map»). **Depende de:** Historia 32 (catálogo de términos) y 4.5. **Tamaño:** M.

## Épica 7: Dejar el producto listo para publicarse con confianza *(nueva, pendiente)*
Un tercero puede confiar en AgentReach, extenderlo y publicarlo. Reúne lo que el análisis del 2026-11-11 mostró sin cubrir.
**Historias:** por escribir (paso 3) · **FR / métricas:** FR-30 (M1), FR-11 (deuda), SM-5, SM-8 · **Estado:** pendiente.

<!-- Historias retroactivas: ficha con enunciado y enlace a su spec. Sus criterios de aceptación completos viven en historias-mvp.md («Terminado cuando») y en implementation-artifacts/spec-historia-N-*.md; no se reescriben aquí. -->

## Épica 1: Ver qué secretos quedan a la vista

El usuario ejecuta `agentreach` sobre una carpeta y ve credenciales, claves y ubicaciones sensibles, sin valores de secretos y con lo no revisado declarado. **Estado: terminada.** FR: FR-4, FR-16, FR-19, FR-25, FR-26. NFR: 1, 2, 3, 10.

### Story 1.1 (Historia 1): Contratos del hallazgo y tubería mínima
Como constructor de AgentReach, quiero un hallazgo con ocho campos y sin ningún campo capaz de guardar un valor, para que ningún detector pueda filtrar un secreto por diseño.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 1») y `spec-historia-1-contratos-y-tuberia.md`. **Estado:** terminada (2026-11-09).

### Story 1.2 (Historia 2): Recorrido del proyecto y enlaces que salen
Como persona que revisa un proyecto, quiero que AgentReach recorra la carpeta sin entrar a lo que hay detrás de un enlace, para que el reporte nunca muestre contenido de fuera del proyecto. FR-19.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 2»), `spec-historia-2-recorrido-y-enlaces.md`. **Estado:** terminada (2026-11-09).

### Story 1.3 (Historia 4): Credenciales en archivos
Como persona que revisa un proyecto, quiero que AgentReach reconozca `.env`, `credentials.json` y similares por nombre o patrón y descarte el valor, para saber dónde están mis secretos sin que el reporte los copie. FR-4.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 4»). **Estado:** terminada (2026-11-09).

### Story 1.4 (Historia 4b): Lectura segura y «no se pudo revisar» con motivo
Como persona que revisa una carpeta de origen desconocido, quiero que un archivo hostil (enorme, tubería, no UTF-8, enlace) no cuelgue ni rompa la herramienta y salga declarado con su motivo, para no creer que algo se revisó cuando no se pudo. FR-25, FR-26.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 4b»), `spec-historia-4b-lectura-segura.md`. **Estado:** terminada (2026-11-09).

### Story 1.5 (Historia 5): Ubicaciones sensibles (SSH, nube, npm)
Como persona que quiere más cobertura, quiero activar de forma voluntaria la revisión de `~/.ssh`, `~/.aws` y `~/.npmrc` con solo metadatos, para saber qué claves de mi equipo quedan al alcance sin que AgentReach abra su contenido. FR-4, AD-9.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 5»), `spec-historia-5-ubicaciones-sensibles.md`. **Estado:** terminada (2026-11-09).

### Story 1.6 (Historia 5b): Primera ejecución completa
Como Alex, quiero ejecutar `agentreach <carpeta>` de punta a punta y ver hallazgos con archivo y línea y la lista de lo no revisado, para comprobar que las piezas ya funcionan juntas.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 5b»), `spec-historia-5b-primera-ejecucion.md`. **Estado:** terminada (2026-11-09); revisión manual de Alex cumplida el 2026-11-09.

### Story 1.7 (Historia 6): Variables de entorno con nombre de credencial
Como persona que revisa su entorno, quiero ver los nombres (nunca los valores) de las variables que parecen credenciales, para saber qué podría heredar un agente. TH-4.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 6»), `spec-historia-6-variables-de-entorno.md`. **Estado:** terminada (2026-11-09).

## Épica 2: Detectar lo que se ejecuta solo o engaña al agente

El usuario sabe si git, los archivos de contexto o el texto invisible pueden hacer que algo se ejecute o que el agente reciba órdenes ocultas, sin que AgentReach ejecute nada. **Estado: terminada.** FR: FR-18, FR-22. NFR: 9.

### Story 2.1 (Historia 7): Git sin ejecutar nada
Como persona que abre un repositorio ajeno, quiero que AgentReach lea `.git/config`, `.gitmodules` y `.gitattributes` como texto y me avise de claves que ejecutan programas y de credenciales en remotos, para saber el riesgo sin dispararlo. FR-22.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 7»), `spec-historia-7-git-sin-ejecutar.md`. **Estado:** terminada (2026-11-09).

### Story 2.2 (Historia 8): Archivos de contexto y scripts de despliegue
Como persona que usa agentes, quiero que AgentReach encuentre archivos de instrucciones (incluso fuera del proyecto) y scripts de despliegue, para saber qué instrucciones y qué acciones de alto impacto tiene a mano un agente.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 8»), `spec-historia-8-contexto-y-despliegue.md`. **Estado:** terminada (2026-11-09).

### Story 2.3 (Historia 16): Caracteres Unicode invisibles
Como persona que confía en sus archivos de instrucciones, quiero que AgentReach detecte texto invisible que un agente lee y yo no veo, sin copiar nunca el mensaje oculto, para no obedecer órdenes que no puedo leer. TH-12.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 16»), `spec-historia-16-invisibles.md`. **Estado:** terminada (2026-11-09).

## Épica 3: Saber con cuánta certeza llega el agente

Cada hallazgo trae su nivel (comprobado, potencial o hipótesis) calculado con los permisos de Windows y las reglas de Claude Code y opencode, «ajeno a la tarea» y el tope por nombre. **Estado: terminada.** FR: FR-5, FR-6, FR-7, FR-8, FR-13, FR-14, FR-15. NFR: 5, 6, 8.

### Story 3.1 (Historia 3): Permisos del sistema en Windows
Como persona que usa Windows, quiero que AgentReach calcule si mi cuenta puede leer un archivo sin abrirlo ni ejecutar `icacls`, para que «comprobado» signifique algo. FR-5, AD-5.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 3» y corrección 3b), `spec-historia-3-permisos-windows.md`. **Estado:** terminada (2026-11-09).

### Story 3.2 (Historia 9): Adaptador de Claude Code
Como usuario de Claude Code, quiero que AgentReach lea mis reglas (usuario, proyecto, local y gestionada) con su precedencia, para que el nivel de cada hallazgo tenga en cuenta lo que Claude Code permite. FR-14.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 9»), `spec-historia-9-adaptador-claude-code.md`. **Estado:** terminada (2026-11-09).

### Story 3.3 (Historia 10): Adaptador de opencode
Como usuario de opencode, quiero que AgentReach lea mi `opencode.json` con la misma calidad que el de Claude Code, para obtener niveles correctos en mi otro equipo. FR-15.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 10»), `spec-historia-10-adaptador-opencode.md`. **Estado:** terminada (2026-11-09).

### Story 3.4 (Historia 10b): opencode 1.x y 2.x
Como usuario de opencode 1.19.0, quiero que el adaptador cubra las versiones 1.x y 2.x, para que mi versión real no dé niveles equivocados. FR-15.
**Criterios de aceptación:** ver `spec-historia-10b-opencode-1x-2x.md`. **Estado:** terminada (2026-11-10).

### Story 3.5 (Historia 17): Configuración del proyecto que se ejecuta sola
Como persona que abre carpetas ajenas, quiero que AgentReach avise de *hooks*, servidores MCP de comando y tareas que corren al abrir la carpeta, para no ejecutar nada sin saberlo. TH-14 a TH-16.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 17»), `spec-historia-17-config-ejecuta-sola.md`. **Estado:** terminada (2026-11-09). *Depende de la Story 3.2.*

### Story 3.6 (Historia 18): Segundo cálculo independiente del permiso
Como persona que depende de un «comprobado», quiero que otra pieza, que no comparte código con la primera, confirme el permiso, para que un error de interpretación de la ACL no pase desapercibido. FR-24.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 18»), `spec-historia-18-verificador-permiso.md`. **Estado:** terminada (2026-11-09).

### Story 3.7 (Historia 11): Cálculo del nivel de confianza y sus invariantes
Como persona que lee el reporte, quiero que cada hallazgo salga comprobado, potencial o hipótesis con su motivo, y que nunca supere el máximo de su tipo, para no confundir «no lo sé» con «sé que no se puede». FR-5 a FR-8.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 11»), `spec-historia-11-nivel.md`. **Estado:** terminada (2026-11-09).

### Story 3.8 (Historia 11b): Correcciones de la revisión de las historias 9 a 11
Como persona que depende de los niveles, quiero que se corrijan los fallos H1 a H4 hallados en la revisión independiente, para que el cálculo no tenga errores conocidos.
**Criterios de aceptación:** ver `spec-historia-11b-correcciones-h1-h4.md`, `review-historias-9-a-11.md`. **Estado:** terminada (2026-11-10).

### Story 3.9 (Historia 11c): Claves repetidas, patrones con `./` o `..` y `.claude` que es un archivo
Como persona con configuraciones raras, quiero que esos casos no engañen al cálculo ni lo rompan, para que un archivo inusual no dé un nivel falso.
**Criterios de aceptación:** ver `spec-historia-11c-claves-patrones-y-claude-archivo.md`. **Estado:** terminada (2026-11-10).

### Story 3.10 (Historia 12): «Ajeno a la tarea»
Como persona que describe su tarea, quiero que AgentReach marque lo que no tiene relación con ella (por el README o `--tarea`), para ver lo que un agente no debería necesitar tocar. FR-9.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 12»), `spec-historia-12-ajeno-tarea.md`. **Estado:** terminada (2026-11-09).

### Story 3.11 (Historia 27): Tope por nombre y letras de las preguntas
Como persona que lee el reporte, quiero que una credencial reconocida solo por su nombre nunca salga «comprobada», para que AgentReach no afirme lo que no pudo ver. FR-7. *(La parte de las letras `(S/N)` y `(Y/N)` es de FR-30, Épica 5.)*
**Criterios de aceptación:** ver `spec-historia-27-letras-y-tope-por-nombre.md`. **Estado:** terminada (2026-11-11). Consecuencias para el código de salida y el oráculo: 13 comprobado, 33 potencial y 2 hipótesis por agente.

## Épica 4: Entender el resultado de un vistazo

El usuario lee el reporte en la terminal y en el navegador, en español o inglés, con color accesible, `doctor` y un flujo diario simple, en **cualquier** terminal. **Estado: terminada; la corrección 4.7 (Historia 29) está construida y revisada, falta tu comprobación en Orca.** Verificaciones manuales de Alex (2026-11-11): 19, 20 y 21 confirmadas; 13b y 13c revisadas en Orca de fondo claro, de donde salieron las dos correcciones. FR: FR-9 a FR-12, FR-17, FR-20, FR-21, FR-23, FR-27, FR-28. UX-DR: 1 a 14.

### Story 4.1 (Historia 13): Reporte con ocho campos, idiomas, orden, autocomprobación y código de salida
Como persona que revisa un proyecto, quiero un reporte ordenado por nivel, con los ocho campos, en español o inglés y con código de salida, para entender cada hallazgo y usarlo en automatizaciones. FR-9 a FR-13, FR-20, FR-21, FR-23, UX-DR8.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 13»), `spec-historia-13-reporte.md`. **Estado:** terminada (2026-11-09).

### Story 4.2 (Historia 13b): Reporte de terminal: ancho, color, codificación y limpieza
Como persona con una consola de Windows, quiero que el reporte no parta palabras, no use el color como única señal y no salga con texto roto, para leerlo sin esfuerzo. FR-27, UX-DR1 a UX-DR3, UX-DR7.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 13b»), `spec-historia-13b-presentacion.md`. **Estado:** terminada (2026-11-09); revisión de Alex en Orca hecha el 2026-11-11 (símbolos correctos).

### Story 4.3 (Historia 13c): Marca, `doctor`, tema y tono
Como persona que usa AgentReach a diario, quiero el banner de marca, `agentreach doctor`, tema claro u oscuro y tono «tú» o formal, para que la herramienta se sienta cuidada y diagnostique mi terminal. UX-DR2, UX-DR4 a UX-DR6.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 13c»), `spec-historia-13c-marca.md`. **Estado:** terminada (2026-11-09); defecto hallado en Orca → Story 4.7.

### Story 4.4 (Historia 19): Reporte HTML estático
Como persona que quiere ver el resultado con calma, quiero un único archivo HTML sin red, por agente y en dos idiomas, para revisarlo en el navegador. FR-28, UX-DR11.
**Criterios de aceptación:** ver `spec-historia-19-reporte-html.md`. **Estado:** terminada (2026-11-10); verificación en navegador por Alex el 2026-11-11: funciona.

### Story 4.5 (Historia 20): Diseño final del reporte HTML
Como persona con muchos hallazgos, quiero tabla, filtros, exportar, imprimir y la vista Recorrido, para trabajar el reporte como programador o auditor. FR-28, UX-DR11, UX-DR12.
**Criterios de aceptación:** ver `spec-historia-20-diseno-final-html.md`. **Estado:** terminada (2026-11-10); confirmada por Alex el 2026-11-11.

### Story 4.6 (Historia 21): Uso diario
Como persona que trabaja en una carpeta, quiero escribir `agentreach` en ella y ver el resumen, el reporte guardado y la pregunta de abrirlo en el navegador, para tener un flujo corto. FR-1 (excepciones), UX-DR10, UX-DR14.
**Criterios de aceptación:** ver `spec-historia-21-uso-diario.md`. **Estado:** terminada (2026-11-10); confirmada por Alex el 2026-11-11.

### Story 4.7 (Historia 29): Colores legibles en cualquier terminal *(terminada 2026-11-11; falta la comprobación de Alex en Orca)*
Como persona con una terminal de fondo claro u oscuro, quiero que AgentReach se adapte solo a los colores de mi terminal, para que nada quede ilegible sin configurar nada. FR-27, UX-DR2. *Origen: en Orca (fondo claro) el «AGENT» del banner era casi invisible, porque sin `COLORFGBG` se asumía fondo oscuro.*

**Criterios de aceptación:**

**Given** no hay `--tema`, ni `AGENTREACH_TEMA`, ni `COLORFGBG`
**When** se muestra el banner o el reporte
**Then** todo texto tiene contraste de al menos 4,5 a 1 contra blanco y contra negro (3 a 1 en las letras grandes del banner)
**And** «AGENT» y «REACH» se leen en ambos fondos.

**Given** `COLORFGBG` indica fondo claro
**When** se muestra
**Then** se usa la variante clara actual, sin cambios.

**Given** `--tema` o `AGENTREACH_TEMA`
**When** se muestra
**Then** la opción explícita gana a cualquier detección.

**Given** la terminal permite consultar su color de fondo
**When** el tema no se pudo detectar por otra vía
**Then** se usa esa respuesta; si no llega en 200 ms o la terminal no la soporta, se usan los colores neutros sin demora visible
**And** la consulta respeta FR-30 (no lee de la entrada estándar sin terminal).

**Given** salida redirigida, `NO_COLOR` o sin terminal
**When** se ejecuta
**Then** no cambia nada (no hay banner).

**And** una prueba mide el contraste de cada color de la marca y del reporte, sin tema detectable, contra blanco y contra negro, y falla si alguno no llega.

**Diseño visual (pedido por Alex el 2026-11-11, referencia `docs/presentacion-terminal/vista-previa/logo-temas.html`):** el logo debe **adaptarse a cada tema de la terminal**, no solo a «claro u oscuro», porque hoy una terminal puede tener casi cualquier color de fondo; y **«AGENT» y «REACH» deben combinar entre sí**: no basta que ambas se lean, se ven como una sola marca.

**Given** cualquier color de fondo, detectado por `COLORFGBG` o por la consulta a la terminal
**When** se dibuja el logo
**Then** «REACH» conserva el **tono menta** de la marca y ajusta solo su luminosidad hasta llegar a 3 a 1 de contraste como mínimo
**And** «AGENT» usa el color neutro de la marca que más contraste da (`#EAF4F2` sobre fondos oscuros, `#0B1114` sobre fondos claros).

**Given** un fondo de tono medio (por ejemplo gris `#808080`)
**When** ningún tono llega al contraste pedido
**Then** se usa el de más contraste **sin perder el tono menta** (luminosidad entre 20 % y 80 %), y nunca queda una palabra casi negra ni casi blanca por empujar el contraste.

**Given** no se pudo saber el color de fondo
**When** se dibuja el logo
**Then** «AGENT» usa el color de primer plano por defecto de la terminal y «REACH» el cian normal del propio tema (no el brillante), de modo que ambos hereden una paleta que el usuario ya eligió para su fondo
**And** el logo no promete el menta exacto en ese caso.

**And** una prueba recorre una lista de fondos reales (blanco, gris claro, Solarized claro y oscuro, Gruvbox claro, GitHub claro, negro, Windows Terminal, Dracula, One Dark, Tokyo Night, gris medio, azul clásico) y comprueba el contraste de cada palabra y que «AGENT» y «REACH» sigan distinguibles entre sí.
**And** una segunda prueba **barre miles de fondos** (una malla de colores RGB, no solo la lista) y comprueba que «REACH» llega a 3 a 1 y conserva el tono menta; donde no es posible (por ejemplo un fondo de tono casi igual al menta) debe caer a los colores del tema y la prueba lo registra, en vez de fallar o dibujar algo ilegible.
**And** el mismo criterio vale para el banner mediano y el mínimo, y para el `doctor`.
**And** *Aprobado por Alex el 2026-11-11 el diseño de la vista previa; la verificación final la hace Alex en Orca (fondo claro) al terminar el cambio.*

*Medición de partida (2026-11-11):* sobre blanco, hoy «AGENT» tiene 1,1:1 y «REACH» 1,4:1; con la propuesta, 19,0:1 y 3,1:1. En fondos oscuros ya cumple.

*Nota:* la consulta del color de fondo no está probada en Orca ni en Windows Terminal; es una exploración dentro de la historia. Si no funciona, bastan las demás capas. **Depende de:** 4.3. **Tamaño:** M.

## Épica 5: Confiar en que la herramienta no daña ni miente

Pruebas bloqueantes de solo lectura, sin red y sin secretos; oráculo de 67 casos; permiso de lectura dado solo por una persona, en dos niveles. **Estado: terminada salvo la Historia 15 (Story 5.2) y la nueva 5.6; la 5.7 (Historia 30) está construida y revisada, falta tu comprobación en Orca.** FR: FR-1, FR-2, FR-3, FR-24, FR-30 (permiso). NFR: 1, 2, 3, 9, 10, 11.

### Story 5.1 (Historia 14): Pruebas de las reglas no negociables
Como persona que confía en la herramienta, quiero pruebas bloqueantes de solo lectura, sin red, sin valores de secretos, sin ejecutar programas y con límites de lectura, para que ninguna regla se rompa sin que algo falle. FR-1 a FR-3.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 14»), `spec-historia-14-reglas-no-negociables.md`. **Estado:** terminada (2026-11-10).

### Story 5.2 (Historia 15): Evaluación contra los 67 casos del oráculo
Como persona que necesita confiar en «comprobado», quiero comparar AgentReach contra los 67 casos de referencia, para detectar comprobados falsos y omisiones. FR-24, SM-1, SM-7.
**Criterios de aceptación:** ver `historias-mvp.md` («Historia 15»), `tests/oraculo/README.md`. **Estado:** construida, **no cerrada** (cierra la Story 5.6). Con `AGENTREACH_PROYECTO_PRUEBA` definida pasan las pruebas del oráculo.

### Story 5.3 (Historia 22): Permiso de lectura, resumen corto y reglas de la terminal
Como persona que opera la herramienta, quiero que AgentReach pregunte antes de leer y muestre un resumen corto, para que solo una persona presente autorice la lectura. FR-30, UX-DR9, UX-DR10.
**Criterios de aceptación:** ver `spec-historia-22-permiso-de-lectura.md`. **Estado:** terminada (2026-11-10).

### Story 5.4 (Historia 23): Arreglos de la revisión de seguridad de la 22
Como persona que depende de la seguridad del permiso, quiero que se cierren los siete fallos de la revisión, para que la pregunta y los archivos escritos no se puedan engañar. FR-30.
**Criterios de aceptación:** ver `spec-historia-23-arreglos-revision-22.md`, `review-historia-22.md`. **Estado:** terminada (2026-11-10).

### Story 5.5 (Historia 28): Permiso en dos niveles
Como persona que protege su carpeta personal, quiero que AgentReach pida un segundo permiso, aparte, antes de ver las reglas de mis agentes fuera del proyecto, para que con «N» no se abra ni se liste nada fuera de la carpeta. FR-30, FR-32.
**Criterios de aceptación:** ver `spec-historia-28-permiso-en-dos-niveles.md`. **Estado:** terminada (2026-11-11).

### Story 5.6 (nueva, pendiente): Cerrar la verificación del oráculo
Como persona que necesita confiar en «comprobado», quiero verificar en fuente primaria los casos esperados como comprobado que siguen sin verificar, para cerrar la Historia 15.

**Criterios de aceptación:**

**Given** los casos esperados como comprobado con `verificado_en_fuente: false` (GT-03, AT-01, AT-03, AT-09, AT-10, GT-19)
**When** se revisa cada uno contra su fuente
**Then** cada uno queda verificado o baja de nivel, con la fuente anotada.

**Given** los demás casos sin verificar
**When** se revisan
**Then** cada uno queda verificado o declarado «regla del PRD».

**Given** la verificación manual de Alex
**When** comprueba un hallazgo con el comando que da el reporte y hace la corrida con opencode real
**Then** queda registrado con fecha.

**And** `historias-mvp.md` deja de decir que falta la confirmación independiente.

**Depende de:** 5.2. **Tamaño:** M.

### Story 5.7 (Historia 30): Todo lo que se imprime respeta el ancho *(terminada 2026-11-11; falta la comprobación de Alex en Orca)*
Como persona con cualquier ancho de terminal, quiero que los textos de bienvenida, las preguntas de permiso y los avisos se ajusten a mi pantalla, para que ninguna palabra salga partida. FR-27, FR-30, UX-DR1. *Origen: en Orca se vio «Solo g / uarda»; esos textos los crearon las Historias 22 y 28 (esta épica) como una línea larga que no pasa por el ajuste del reporte. Por eso vive aquí y no en la Épica 4: depende de la Story 5.5.*

**Criterios de aceptación:**

**Given** anchos de 60, 80, 100 y 140 columnas
**When** se muestran la bienvenida, las dos preguntas de permiso, los avisos y el «reporte guardado en…»
**Then** ninguna línea pasa del ancho menos uno ni parte una palabra (salvo una ruta indivisible).

**Given** español e inglés, tono cercano y formal
**When** se muestran esos textos
**Then** se cumple en las cuatro combinaciones.

**Given** un ancho menor de 40
**When** se muestran
**Then** no hay error y el texto sigue legible.

**And** una prueba captura **toda** la salida de un flujo completo (no solo el cuerpo del reporte) y le aplica la comprobación de ancho.

**Depende de:** 4.2 y 5.5. **Tamaño:** S.

## Épica 6: Saber qué agentes hay y por qué algo no se determinó

El usuario ve los agentes configurados, qué analiza AgentReach y qué solo reconoce, y el archivo y la clave que impiden un nivel, **explicado en lenguaje llano**. **Estado: terminada salvo la paridad con el README (Historia 34); el HTML (Historia 33) está construido y revisado, falta tu comprobación en el navegador.** FR: FR-11, FR-29, FR-31, FR-32. UX-DR: 13, 15.

### Story 6.1 (Historia 24): Reconocer los agentes configurados con el catálogo
Como persona con varios agentes, quiero ver cuáles están configurados, sin que se diga que se ejecutaron, para saber qué entornos tiene mi equipo. FR-29, FR-31, UX-DR13.
**Criterios de aceptación:** ver `spec-historia-24-agentes-configurados.md`. **Estado:** terminada (2026-11-10).

### Story 6.2 (Historia 25): Por qué un nivel es «no determinado»
Como persona que ve muchos «potencial», quiero saber qué archivo y qué clave impiden el nivel, sin valores, para saber qué revisar a mano. FR-32.
**Criterios de aceptación:** ver `spec-historia-25-por-que-no-determinado.md`. **Estado:** terminada (2026-11-10).

### Story 6.3 (Historia 26): GitHub Copilot, un solo agente cuando la señal es compartida
Como persona que usa Copilot, quiero que se reconozca un solo agente cuando la única señal es compartida, para que no se afirme una superficie que no se sabe. FR-31.
**Criterios de aceptación:** ver `spec-historia-26-github-copilot-un-agente.md`. **Estado:** terminada (2026-11-10). Deuda: el nombre va solo en español (→ Story 7.2).

### Story 6.4 (Historia 32): El reporte explica cada término técnico en lenguaje llano *(parte de terminal terminada 2026-11-11; falta tu comprobación en Orca; HTML = Historia 33 y README = Historia 34, pendientes)*
Como persona que no es experta en seguridad, quiero que el reporte me diga qué es y qué significa **para mí** cada término técnico que aparece (nivel, «no determinado», *hook*, *sandbox*, agente «configurado», «no se pudo revisar»), para decidir qué hacer sin buscar nada fuera. FR-11, FR-32, UX-DR15. *Origen: en la prueba real de Alex (2026-11-11), con sus *hooks* `PreToolUse`, el resumen decía «16 hallazgos sin nivel determinado · hooks.PreToolUse · función que AgentReach no modela» y no explicaba qué es un *hook* ni qué implica; y «se corrigieron 1 hallazgo(s) … autocomprobación» no decía cuál ni por qué.*

**Criterios de aceptación:**

**Given** un resumen con niveles «no determinado» por `hooks.PreToolUse`
**When** se imprime en la terminal
**Then** explica en una o dos frases qué es un *hook* y por qué impide el nivel, dice que **no significa que sea inseguro**, y no usa expresiones internas como «no modela».

**Given** cualquier término del conjunto fijo (los tres niveles, «no determinado», «no se pudo revisar», *hook*, *sandbox*, agente «configurado» y «analizado», autocomprobación)
**When** aparece en la terminal o en el HTML
**Then** tiene un «qué es» y un «qué significa para ti» tomados de **un solo catálogo fijo**, en español e inglés y en tono cercano y formal (FR-11).

**Given** la terminal
**When** se imprime el resumen
**Then** sigue siendo corto (Historia 22): como máximo una frase por término; la explicación completa sale con `--detalle` y en el HTML.

**Given** el HTML
**When** se abre
**Then** incluye una sección plegable «Cómo leer este reporte» con los mismos términos y un ejemplo de cada nivel, por agente.

**Given** un hallazgo corregido por la autocomprobación
**When** se informa
**Then** dice en lenguaje llano **cuál** hallazgo (tipo y ruta, sin valores) y por qué cambió de nivel.

**Given** el README
**When** se comparan sus definiciones con el catálogo
**Then** cada término del catálogo está definido en el README con el mismo sentido (una prueba lo comprueba).

**And** una prueba falla si en el resumen de la terminal aparece un identificador técnico (`hooks.PreToolUse`, `funcion_no_modelada`, `TH-n`) sin su explicación al lado, salvo con `--detalle`.

**Fuente de diseño:** `ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md` (glosario de 11 fichas con los textos en tú, usted e inglés, reglas de cuándo y dónde aparece cada explicación, y dependencias técnicas) y `DESIGN.md` (colores y componentes). **División acordada:** la Historia 32 construye el catálogo de términos, la autocomprobación que dice cuál hallazgo y la **terminal**; el HTML «Cómo leer este reporte» es la Historia 33 (Story 6.5) y la paridad con el README la Historia 34 (Story 6.6), pendientes. **Depende de:** 4.1, 4.5 y 6.2, y de un cambio de código: `gate.py` descarta hoy la ubicación, el tipo y el nivel de cada hallazgo corregido por la autocomprobación. **Tamaño:** L (partir en terminal, HTML y README si la primera pasada falla).

## Épica 7: Dejar el producto listo para publicarse con confianza *(nueva, pendiente)*

Un tercero puede confiar en AgentReach, extenderlo y publicarlo. Reúne lo que el análisis del 2026-11-11 mostró sin cubrir. **Estado: pendiente.** FR / métricas: FR-30 (M1), FR-11 (deuda), SM-5, SM-8.

### Story 7.1: El oráculo corre en la suite por defecto
Como mantenedor, quiero que `pytest` corra el oráculo aunque no esté definida `AGENTREACH_PROYECTO_PRUEBA`, para que SM-1 y SM-7 no se omitan en silencio.

**Criterios de aceptación:**

**Given** la variable no está definida
**When** se ejecuta `pytest`
**Then** el proyecto de prueba se genera en una carpeta temporal con `pruebas/generar_proyecto_prueba.py` y el oráculo corre, sin `skip`.

**Given** el entorno no puede crear enlaces simbólicos
**When** corre el oráculo
**Then** EN-03 se omite y se declara «no aplicable», sin fallar.

**And** la prueba no escribe fuera de la carpeta temporal y no deja nada atrás.

*Condición previa:* verificar que el generador admite una ruta de salida temporal. **Tamaño:** M.

### Story 7.2: Nombres de agentes bilingües
Como persona que usa AgentReach en inglés, quiero que el nombre de cada agente reconocido salga en mi idioma, para cumplir FR-11.

**Criterios de aceptación:**

**Given** el catálogo de agentes
**When** se recorren todos los nombres
**Then** cada uno existe en español y en inglés, incluido «GitHub Copilot (VS Code o su línea de comandos)».

**And** una prueba falla si algún nombre falta en uno de los dos idiomas.

**Tamaño:** S.

### Story 7.3: Medir la determinabilidad en una configuración real (SM-8)
Ficha. Informe con el porcentaje de hallazgos determinables en la configuración real de Alex y la clave que impide los demás. **Bloqueada por:** pregunta 31 (umbral); se puede hacer sin umbral. **Tamaño:** S.

### Story 7.4: Confirmación desde la terminal real (M1)
Ficha. Leer la confirmación de `CONIN$` o `/dev/tty` y registrar el modo de ejecución en el reporte; prueba por tubería, pseudoterminal y variable de entorno de un agente. **Bloqueada por:** decisión de alcance de Alex. **Tamaño:** L.

### Story 7.5: Adaptadores de terceros (SM-5)
Ficha. Guía para escribir un adaptador y mecanismo de registro (hoy no existen *entry points*), con un adaptador de ejemplo añadido sin tocar el núcleo. **Bloqueada por:** decisión de diseño. **Tamaño:** L.

### Story 7.6: `--redact-paths`
Ficha. Decidir si va activado por defecto (pregunta 9) y construirlo. **Bloqueada por:** decisión de Alex. **Tamaño:** M.

### Story 7.7: Preparar el repositorio público
Ficha. Pregunta 30 (`_bmad-output/` y licencia de `.claude/`), `main` como instantánea limpia, revisión de secretos y releer las fuentes «secundaria». **Bloqueada por:** decisión de Alex. **Tamaño:** M.
