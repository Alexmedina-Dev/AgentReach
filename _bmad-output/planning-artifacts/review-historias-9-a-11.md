# Revisión independiente, historias 9 a 11 (adaptadores de Claude Code y opencode, nivel de confianza)

Revisor: agente de solo lectura. Fecha: 2026-11-10. Esta copia reemplaza a la que iba en
`_bmad-output/planning-artifacts/review-historias-9-a-11.md`: el worktree aislado desapareció durante la pausa,
así que el informe quedó en la carpeta temporal de la sesión.

## Resultados reales (ejecutados)
- `uv run pytest -q`: 959 pasaron, 54 omitidas, 0 fallaron.
- `uv run ruff check src tests`: todo en orden.
- Los contraejemplos de abajo se ejecutaron con `auditar()` sobre carpetas temporales propias, en Windows.
  Se usó un valor falso (CANARIO) y no se imprimió ningún valor de secreto.
- No se ejecutó nada de `trampas*` ni se tocó `proyecto-prueba-agentreach`.
- No se llegó a ejecutar el guion `e3.py` (opencode: permisos por agente, claves duplicadas, usuario con opt-in activado)
  porque el worktree se borró. Esos puntos quedan solo leídos.

## Veredicto
No aprobado todavía. El núcleo de `nivel.py` e `invariantes.py` es sólido y prudente: la tabla de FR-5, el deny a
potencial, la herencia que no baja, sin fuente verificada a potencial y la discrepancia a potencial están bien y
cubiertas. Pero el paso entre adaptador y evaluador convierte "no pude leer la regla" en "no hay regla", y eso produce
un "comprobado" falso (SM-1, el fallo más grave del PRD).

## Hallazgos críticos y altos

### H1. CRÍTICA. Configuración del agente ilegible se trata como "sin regla" y el nivel queda comprobado
- Archivos: `src/agentreach/adapters/claude_code/__init__.py` líneas 166-187 y 298-305 (`postura_para`);
  `src/agentreach/core/evaluador.py` `_para_agente`.
- Escenario ejecutado: `.env` legible más `.claude/settings.json` con `deny Read(./.env)`, pero el JSON está
  - con un comentario `//`,
  - cortado,
  - en UTF-8 inválido,
  - con un elemento que no es texto (`["Read(./.env)", 5]`), o
  - con más de 10 MB.
  En los cinco casos el resultado fue claude_code `comprobado`, motivo `existe_legible_sin_regla`, postura `sin_regla`.
  El `NoRevisado` sale en otra lista y no baja el nivel.
- Contradice FR-5 (si la regla no se puede determinar, es potencial) y SM-1.
- Es el ataque más barato: un archivo de configuración "roto a propósito" en el repo auditado.
- Arreglo: que `cargar` marque el adaptador como "reglas incompletas" cuando una fuente existe y no se pudo leer o
  interpretar. Con eso `postura_para` devuelve `NO_DETERMINADA` para todo (o para lo que la fuente pudo alcanzar), y
  `calcular` ya lo manda a potencial. Lo mismo en opencode (`_reglas_de`).
- Prueba que falta: una por cada motivo de `NoRevisado` de configuración.

### H2. ALTA. Fuentes que no se leen (usuario, gestionada) tampoco bajan el nivel
- Archivos: `claude_code/__init__.py` líneas 108-117; `opencode/__init__.py` líneas 126-139.
- Con el opt-in apagado (el valor por defecto), un `deny` en `~/.claude/settings.json` o en la configuración gestionada
  no se ve. El `.env` sale comprobado con postura `sin_regla`. Verificado solo leyendo el código y el ejemplo
  `usr_deny` (no se llegó a correr).
- En opencode la gestionada es la última y manda: un `deny` ahí anularía cualquier `allow` del proyecto.
- Decisión pendiente para Alex. El oráculo puede esperar comprobado con el opt-in apagado (SM-7), pero entonces el
  reporte debe decir "comprobado solo con la configuración del proyecto", y hoy no lo dice en el hallazgo.
- Mínimo: nota en el hallazgo, o motivo "regla no determinada" cuando la fuente existe en disco. Para saber si existe
  basta con mirar los metadatos de la ruta, sin abrir el archivo.

### H3. ALTA. Los patrones `Read(...)` de Claude Code no siguen la semántica tipo gitignore
- Archivo: `claude_code/reglas.py` líneas 39-66 y 84-103.
- Ejecutado: `deny Read(*.env)` con `config/prod.env` sale comprobado, porque el patrón sin barra se ancla a la raíz.
  En el formato gitignore que usa Claude Code, un patrón sin barra coincide en cualquier profundidad.
  Confirmar con la documentación actual de Claude Code: se leyó de memoria, no se verificó.
- Ejecutado: `Read(.\sec\**)` (barras de Windows) no coincide, porque en `coincide` no se normaliza `\`.
- Ejecutado: `Read(./.en[v])` (clases con corchetes) se ignora.
- Ejecutado: `Read()` no alcanza nada.
- Los cuatro casos dan falso comprobado. Los patrones que no se saben interpretar deberían dar postura no determinada,
  nunca "no coincide".
- Arreglo: tratar el patrón sin `/` como `**/patrón`, convertir `\` en `/`, y si el patrón tiene `[`, `{` o `!` o queda
  vacío, devolver "no determinado".

### H4. ALTA. Reglas por agente de opencode ignoradas (`agent.<nombre>.permission`)
- Archivo: `opencode/__init__.py` líneas 183-186.
- Solo se agrega un `NoRevisado`; las reglas del agente se descartan. El PRD (FR-17) dice que el orden es base,
  global y agente. Un `deny` por agente sobre `.env` deja el `.env` comprobado.
- Solo leído (el guion no llegó a correrse).
- Arreglo: igual que H1, tras ese `NoRevisado` el adaptador debe devolver postura no determinada. Mejor aún, modelar el
  permiso por agente.

### H5. ALTA (ya planeada como 10b). El adaptador de opencode asume 2.x y el usuario tiene 1.19.0
- Archivo: `opencode/__init__.py` líneas 1-26.
- En 1.x existen las claves `tools: {read: false}` y otro esquema de `permission`.
- Hoy las claves `tools` se ignoran sin avisar, así que el `.env` queda comprobado aunque el agente tenga `read`
  apagado. No se probó (opencode no está instalado en este equipo).
- Hasta la 10b: en el reporte, el resultado de opencode debe decir "esquema 2.x asumido". No debe poder llegar a
  comprobado si hay una clave `tools` o `mode` desconocida.

## Hallazgos medios y bajos

### M1. MEDIA. Comparación de rutas frágil
- Archivo: `claude_code/reglas.py` línea 86.
- Ejecutado: un patrón absoluto `//C:/Users/<usuario>/...` no coincide con una carpeta abierta por su
  nombre corto 8.3 (`<USUARIO~1>`). Con la misma forma sí coincide.
- Se usa `abspath`, no la ruta real ni el nombre largo, y los enlaces y junctions no se resuelven.
- En el escenario "proyecto abierto vía junction" el deny sí coincidió.
- No se pudo crear un enlace simbólico de archivo (falta privilegio), así que el caso de `ruta_real` fuera del proyecto
  queda solo leído. `evaluador.py` `_para_agente` consulta la regla con `ruta_real`, así que un `deny` escrito contra
  el nombre del enlace podría no coincidir con el destino. Debería probarse con ambas rutas y tomar la postura más
  restrictiva.

### M2. MEDIA. Falta cobertura del oráculo en las pruebas
- Solo hay pruebas por reglas sueltas. No hay una prueba de extremo a extremo "configuración ilegible, nivel potencial"
  (H1), ni de patrones sin barra o con `\` (H3), ni de `agent.*.permission` (H4).
- El oráculo documenta PP-01 por agente, y esto sí está cubierto.
- Pasan por la razón correcta: `test_nivel.py` prueba la tabla con hechos falsos, lo cual es correcto, pero nada prueba
  la entrada de esos hechos desde un adaptador degradado.

### M3. MEDIA. Autocomprobación no atrapa H1
- Archivo: `invariantes.py`.
- `COMPROBADO_REGLA_NO_DETERMINADA` solo se activa si la postura es `NO_DETERMINADA`, y H1 produce `SIN_REGLA`.
- La segunda mirada comparte la misma entrada errónea, así que no sirve de red para este fallo.

### B1. BAJA. `deny Edit` o `deny Bash(cat .env)` no bajan el nivel
- Conducta defendible y coherente con "el sistema de permisos no es un sandbox" (FR-6). No es un error; anotarlo en
  la documentación.

### B2. BAJA. Cada hallazgo de archivo sale duplicado por agente aunque no haya configuración de ese agente
- Coherente con FR-17 y el oráculo. Se anota para el reporte: aclarar "sin configuración de este agente en el
  proyecto".

## Verificado en cada punto
- **Solo lectura, sin red y sin ejecutar programas:** solo leyendo. Los adaptadores usan `FsSoloLectura` y no importan
  `subprocess` ni `socket`. No se encontró violación.
- **Impresión de secretos:**
  - Ejecutado: se auditó con un valor CANARIO en `.env`; el informe de pruebas no lo imprimió.
  - Leído: `Regla.especificador` va con `repr=False`.
  - No revisado: los mensajes de las excepciones del adaptador.
- **JSON con comentarios, UTF-8 inválido, archivo enorme y forma rara en Claude Code:** ejecutado. No lanzan y salen en
  `NoRevisado`, pero con el efecto de H1.
- **Precedencia en Claude Code:**
  - Ejecutado: local deny sobre proyecto allow da deny; allow más ask da ask.
  - Ejecutado: deny gana a allow.
  - Las fuentes usuario y gestionada: solo leído.
- **Mayúsculas y minúsculas en Windows:** ejecutado, bien (`./.ENV` coincide con `.env`).
- **Opencode, última coincidencia:** solo leído; `_ultima_coincidencia` hace lo correcto. El caso `base_sin_reglas`
  (ask de la base, potencial) sí se ejecutó.
- **Junction hacia carpeta externa:** ejecutado. No se sigue ni se emite hallazgo del `.env` de adentro.

## Qué falta para aprobar
1. Resolver H1 y H2, con pruebas de extremo a extremo.
2. Corregir H3 (semántica del patrón) con casos de oráculo, y cerrar H4 y H5.
3. Revisar con Alex si "comprobado con el opt-in apagado" es lo esperado (SM-7).
4. Volver a correr `e3.py` (guion de opencode) tras los arreglos.

## Estado de las correcciones (2026-11-10)

H1 a H4: corregidos en la Historia 11b (`spec-historia-11b-correcciones-h1-h4.md`); H2 con la opcion A de Alex. M1 (rutas 8.3 y enlaces) y M2/M3 (cobertura y autocomprobacion) cubiertos en parte. H5 (opencode 1.x) queda para la 10b.
