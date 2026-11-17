---
status: propuesta (sin aprobar)
fecha: 2026-11-17
modo: por lotes
alcance: moderado, con la excepción de la Historia 31 como decisión de producto (PM y arquitecto)
toca-codigo: no
---

# Propuesta de cambio de rumbo — 2026-11-17

## 1. Resumen del problema

Alex pide tres cambios:

1. **Ramas.** El trabajo pasa a la rama `development` por Pull Request (PR). `PruebaAlex` queda como archivo (solo lectura histórica).
2. **Historias que se rehacen en `development`:** 31, 40, 41, 42, 43, 44 y 46.
3. **Excepción de la Historia 31.** El aviso de versión puede usar red y lanzar un programa, y solo en ese aviso. Decisión de Alex, «entrada 152 del registro».

### Lo que encontré al comprobarlo (hay que resolverlo antes de aprobar)

| # | Hallazgo | Evidencia | Qué necesito |
|---|---|---|---|
| A | **La entrada 152 no existe.** El registro del PRD (`prds/prd-agent-reach-2026-11-05/.memlog.md`) tiene 147 líneas, en `development` y en `origin/PruebaAlex`. | `wc -l` en ambas ramas; no hay «152» en ningún `.md` de ninguna rama. | Que se registre la decisión (la anoto yo al aprobar) o que me indiques dónde está. |
| B | **Las historias 40–44 y 46 no existen en ningún documento.** El plan llega a la 33 (`epics.md`), la 34 está solo anotada en `deferred-work.md`. Tampoco hay specs 31 ni 35–46 en `development` ni en `origin/PruebaAlex`. | `git ls-tree` de las dos ramas. | Una línea por historia (qué hacía). No invento su contenido; van como fichas vacías. |
| C | **La Historia 31 ya tiene otro significado.** En `deferred-work.md`, `ARCHITECTURE-SPINE.md` y `EXPERIENCE.md` es «detectar el color de fondo de la terminal (OSC 11)». Tú la describes como «aviso de versión». | Ver `deferred-work.md` (Historia 31) y AD-20. | Elegir: (a) la 31 pasa a ser el aviso de versión y la detección de fondo recibe un número nuevo (mi recomendación, porque tu decisión es la más reciente) o (b) el aviso de versión recibe otro número. |
| D | **No existe archivo `sprint-status`.** El avance vive en `epics.md` (estados por historia) y en `memory/00-proyecto-estado.md`, que está **desactualizado desde 2026-11-09** y aún dice «rama de trabajo PruebaAlex… no hacer commit ni push sin que Alex lo pida». | Archivo leído. La decisión de planificar el sprint «después de las pruebas» está en el registro. | Confirmar que «estado del avance» = esos dos archivos. |
| E | Hoy `PruebaAlex` tiene **1 commit que `development` no tiene** (`a64d9a3`, documentos del mantenedor), y `development` tiene 7 que `PruebaAlex` no. | `git log` entre ramas. | Decidir si ese commit se trae a `development` antes de archivar. |

## 2. Análisis de impacto

**Épicas**
- E4 (terminal y HTML): la 31, según la opción C, deja de ser «detección de fondo» y esa historia se renumera.
- E7 (listo para publicar): el aviso de versión toca la 7.7 (preparar el repositorio público) y el riesgo de privacidad. La Story 7.4 (M1, confirmación desde la terminal real) se vuelve más importante: el permiso de red debe venir de una persona.
- Historias 40–44 y 46: sin épica asignable hasta saber qué son (B). Propongo un hueco provisional en E8 «Rehacer en `development`».

**Requisitos del PRD que chocan con la excepción** (hoy dicen «sin excepciones»)
- FR-1 (nota del 2026-11-09, «no ejecuta ningún programa externo, sin excepciones») y su punto 2 «Qué se lanza».
- FR-2 («no hay excepciones… ni modo con red»), §5 (línea de reglas transversales), §6 (no objetivos), SM-4, pregunta 19 (cerrada como «sin red, sin excepciones»).
- En las épicas: FR-1, FR-2, NFR-2, NFR-9 y AD-4 (sin red por ausencia estructural).
- `CONTRIBUTING.md`, regla 1 («durante la revisión no lanza programas»), y el `README`.

**Pruebas que hoy se romperían por diseño (no las toco; quedan en la historia 31):** `tests/reglas_no_negociables/test_sin_red.py` (bloquea sockets), `test_sin_ejecutar_programas.py` (reemplaza `subprocess` y familias) y `test_reportes_y_navegador.py` (hay un patrón a imitar: `webbrowser` solo en `infra/navegador.py`).

**Flujo de trabajo:** `CONTRIBUTING.md` ya apunta los PR a `development`; solo falta la fila de `PruebaAlex`. La memoria del proyecto manda a trabajar en `PruebaAlex`.

## 3. Enfoque recomendado: ajuste directo

- Es un ajuste de plan, sin deshacer trabajo terminado. El único cambio de fondo es la excepción, que modifica dos reglas «no negociables». Por eso la apruebas tú explícitamente y la registro como decisión.
- Esfuerzo de documentos: bajo (media jornada). Riesgo principal: que «solo en el aviso de versión» se ensanche con el tiempo. Se mitiga con barreras comprobables por prueba (§4.1).

## 4. Cambios propuestos (antes → después)

### 4.1 PRD

**FR-1, nota del 2026-11-09 — añadir al final:**

> **Excepción única (decidida por Alex, entrada 152 del registro; Historia 31):** el aviso de versión. Es la *única* ocasión en que AgentReach usa red o lanza un programa. Barreras, cada una con prueba: (1) solo con permiso de una persona en terminal interactiva, igual que la lectura (FR-30), y nunca en CI ni sin terminal; (2) solo fuera de la revisión: ni antes ni durante la lectura; (3) un único módulo la contiene, como `infra/navegador.py`; (4) no envía nada del proyecto, ni rutas, ni hallazgos, ni identificador; (5) tiempo máximo corto y, si falla, la revisión sigue y el código de salida no cambia; (6) se apaga con `--sin-aviso` y con una variable de entorno; (7) el reporte declara que se hizo. *[Pendiente de confirmar con Alex: el programa que se lanza y a qué dirección se conecta; lo escribí en forma de barreras porque no tengo la historia.]*

**FR-1, punto 2 «Qué se lanza» — cambiar:**
- ANTES: «Durante la revisión, ningún programa (sin cambios).»
- DESPUÉS: «Durante la revisión, ningún programa (sin cambios). Fuera de ella, solo el navegador (arriba) y el aviso de versión (Historia 31, excepción acotada).»

**FR-2 — cambiar:**
- ANTES: «No hay excepciones en el MVP: tampoco existe un modo "con red" (decidido por Alex el 2026-11-09).»
- DESPUÉS: «Una sola excepción, decidida por Alex (entrada 152): el aviso de versión, con las barreras de FR-1. **Durante la revisión sigue sin haber red, y no existe un modo "con red" para revisar.** La prueba de sockets sigue bloqueando la auditoría completa; el aviso se prueba aparte.»

**§5, primera viñeta:** ANTES «Sin red no admite excepciones en el MVP.» → DESPUÉS «Sin red durante la revisión; la única excepción es el aviso de versión (FR-2).»

**§6, viñeta «No ejecuta ningún programa externo»:** añadir «(salvo el aviso de versión, FR-1)».

**SM-4:** «Se ejecuta sin red… (prueba automática, FR-2)» → añadir «durante la revisión; el aviso de versión se prueba aparte».

**§10, pregunta 19:** dejar «CERRADA» y añadir la nota «reabierta solo para el aviso de versión por la entrada 152».

**§5.1 (nuevo punto, privacidad):** «El aviso de versión revela a quien responde que alguien con esa IP usa AgentReach; por eso es opt-in y se declara en el README.»

**Cabecera:** `version: "0.2 …"` → `"0.3 — ramas por PR y excepción del aviso de versión"`, `updated: 2026-11-17`.

### 4.2 Épicas (`epics.md`)

- **FR-1 y FR-2 del inventario y NFR-2/NFR-9:** mismos textos que el PRD, con la excepción. **AD-4:** «sin red por ausencia estructural» → «ausencia estructural en la revisión; el aviso vive aislado en un módulo con lista blanca».
- **Resumen:** quitar «No reabre ni rehace nada» → «Las historias 31, 40–44 y 46 se rehacen en `development`; el resto conserva su número, spec y estado».
- **Mapa de cobertura:** FR-1 y FR-2 pasan de «Hecho (14, 21, 22)» a «Hecho; excepción pendiente (31)».
- **Story 4.8 (Historia 31): Aviso de versión** *(nueva; sustituye a «detección de fondo», que se renumera: opción C)*. Criterios de aceptación propuestos, a completar con Alex:
  - **Given** terminal interactiva y revisión terminada **When** hay versión nueva **Then** se avisa en una frase y solo con permiso de una persona.
  - **Given** sin terminal, CI, `--sin-aviso` o su variable **Then** no hay red ni programa.
  - **Given** la prueba de sockets de la auditoría **Then** sigue pasando: ninguna conexión durante la revisión.
  - **Given** falla o tarda **Then** no cambia el reporte ni el código de salida.
  - **And** prueba de que la red y el programa solo se tocan desde un módulo, y de que nada del proyecto sale.
  - Depende de 4.6 (uso diario) y de 5.3 (permiso). Tamaño: M.
- **Historia de detección de fondo (OSC 11):** nuevo número (propongo 35, si está libre) como Story 4.9; el texto de `deferred-work.md` se actualiza.
- **Épica 8 «Rehacer en `development`» (provisional):** fichas para 40, 41, 42, 43, 44 y 46, cada una «por redactar con Alex» (hallazgo B).
- **Story 7.7:** añadir «`PruebaAlex` queda como archivo; `main` como instantánea limpia desde `development`».

### 4.3 Estado del avance (`memory/00-proyecto-estado.md`)

- **Repositorio / rama de trabajo:** ANTES «Rama de trabajo: `PruebaAlex`… no empujar a `main`». DESPUÉS «Se trabaja en `development` por PR (rama propia → PR a `development`). `PruebaAlex` es archivo: no se empuja. `main` solo por decisión de Alex».
- **Cómo retomar, punto 4:** «No hacer commit ni push sin que Alex lo pida» → conservar el permiso pero cambiar «(rama `PruebaAlex`)» por «(rama propia hacia `development`)».
- **Bloque «Estado del flujo BMAD»:** hoy habla de «17 historias» y «esqueleto»; pasa a «historias 1 a 30, 32 y 33 hechas; por rehacer en `development`: 31, 40–44, 46; pendientes: 34 y E7».
- **Reglas no negociables:** «Sin red por defecto» → «Sin red durante la revisión; excepción única: aviso de versión (Historia 31)».
- **Cabecera:** fecha 2026-11-17.
- **Porcentaje de avance** (tu preferencia): no lo recalculo hasta saber qué son 40–46; **no inventaré un número**.
- **Archivo `sprint-status.yaml`:** no se crea ahora. Cuando se planifique el sprint, se genera ya con `development` como rama y con las siete historias en «por rehacer».

### 4.4 Otros archivos que quedan desfasados (solo aviso)

`CONTRIBUTING.md` (fila de `PruebaAlex`: «es la rama de trabajo» → «archivo»; regla 1), `README.md`, `ARCHITECTURE-SPINE.md` (AD-4, AD-20) y `deferred-work.md` (Historia 31). Los ajusto al aprobar, o los dejo a la historia 31 si prefieres.

## 5. Entrega y siguiente paso

- **Alcance: moderado.** Pasa por reorganizar el plan (PO/DEV) y por una decisión de producto sobre dos reglas no negociables (PM, John, y arquitecto, Winston, para AD-4).
- **Éxito:** PRD, épicas y estado dicen lo mismo; ningún documento afirma «sin excepciones»; las siete historias figuran como «por rehacer en `development`»; el aviso tiene barreras comprobables por prueba.
- **No toqué código ni apliqué estos cambios a los documentos de origen.**

## 6. Lo que necesito de Alex para cerrar

1. ¿La entrada 152 la registro yo en el `.memlog.md` (texto exacto de la decisión)?
2. Una línea por cada historia 40, 41, 42, 43, 44 y 46.
3. Opción A o B para la historia 31 (aviso de versión vs. detección de fondo).
4. ¿Qué programa lanza el aviso y a qué dirección se conecta?
5. ¿El commit `a64d9a3` de `PruebaAlex` se trae a `development`?
6. ¿Apruebo y aplico los cambios a PRD, épicas y estado? (sí / no / revisar)
