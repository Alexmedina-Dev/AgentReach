# Propuesta de cambio de sprint — Primera corrida real de AgentReach

**Fecha:** 2026-11-11 · **Proyecto:** agent-reach · **Autor del cambio:** Alex · **Modo de revisión:** incremental (cada propuesta decidida una por una)
**Origen:** `research/technical-agentreach-reporte-proyecto-real-local-2026-11-11/research.md` (R1 a R8)
**Estado:** aprobada por Alex y aplicada el 2026-11-11 (epics.md, PRD §7.2 y pregunta 9, deferred-work.md y sprint-status.yaml)

## 1. Resumen del problema

El 2026-11-11 a las 17:33 AgentReach 0.1.0 revisó por primera vez un proyecto real ajeno (`proyecto real local`, 2089 archivos) y produjo 12 hallazgos: 0 Comprobado, 10 Potencial y 2 Hipótesis. La corrida mostró fricción de uso: hallazgos repetidos entre agentes, un posible falso positivo, cajas vacías en el camino de alcance, mezcla de idiomas en el HTML y un agente (opencode) con hallazgos sin figurar como configurado.

**Tipo de cambio:** aprendizaje de campo, no un fallo de una historia concreta. Es la misma clase de evidencia que el SM-8.

**Evidencia (verificada contra los datos embebidos del reporte):** `rule=null` y `source_verified=false` en 12 de 12 hallazgos; `ORCA_PANE_KEY` presente como hallazgo; `html lang="en"` junto a `initial_language=es`. Sin verificar todavía: evidencia de «configurados» truncada, y el filtro del nivel «No se pudo revisar».

**Corrección importante frente al informe de investigación:** los 0 Comprobados **no se deben solo a los hooks**. Por la Historia 27 (AD-11), una credencial reconocida solo por su nombre nunca pasa de Potencial. Modelar `PreToolUse` no los subiría. El reporte hizo lo que FR-32 y AD-12 piden: dice «no determinado» y señala archivo y clave, sin valores.

## 2. Análisis de impacto

| Área | Impacto |
|---|---|
| **MVP** | No se compromete. Ningún cambio toca los criterios de §7.3. |
| **Épica 3** (adaptadores y nivel) | 1 historia nueva (R3). |
| **Épica 4** (reporte) | 1 historia nueva (R2). |
| **Épica 6** (agentes y «no determinado») | 2 historias nuevas (R4, R8) y 1 ampliada (35, por R6). |
| **Épica 7** (publicar con confianza) | Sin historia nueva: R5 suma evidencia a la 7.6 (`--redact-paths`), ya bloqueada por la pregunta 9. |
| **PRD** | §7.2 (nota de Fase 2, por R1) y FR-31 (regla nueva, solo si R8 se confirma). FR-3, FR-17 y FR-32 no cambian. |
| **Arquitectura** | Sin cambio de decisiones. AD-11 y AD-12 se confirman. AD-15, AD-16 y AD-17 se tocan solo en su implementación. |
| **UX** | `EXPERIENCE.md`: marca «también en» (R2), caja de efecto (R4) y modo para compartir (R5). |
| **Código** | Catálogo de explicaciones, plantilla HTML, compuerta (vista), detector de nombres (condicionado) y CLI (opción de compartir). |

## 3. Enfoque recomendado

**Ajuste directo** (opción 1 de la lista de opciones): agregar y ampliar historias dentro de la estructura de épicas actual. No hay reversión ni cambio del MVP.
- **Esfuerzo:** bajo a medio (5 historias, casi todas de tamaño S).
- **Riesgo:** bajo. Ninguna cambia el cálculo del nivel ni las reglas no negociables, salvo R3, que está condicionada a evidencia.
- **Calendario:** sin impacto en el cierre del MVP; las historias pueden ir después de las pendientes 34 a 36.

**Alternativas descartadas:** modelar `hooks.PreToolUse` ahora (lógica nueva y de riesgo para SM-1, ver R1); colapsar hallazgos entre agentes (contradice FR-17, ver R2).

## 4. Cambios propuestos (todos aprobados en el modo incremental)

### Historias

| # | Origen | Cambio | Dónde |
|---|---|---|---|
| 1 | R2 | **Nueva, historia 37** «Un mismo archivo y línea que sale en varios agentes lo dice»: cada hallazgo muestra «también en: <agente>» si coinciden ubicación y tipo. No cambia `Finding` ni el nivel. | Épica 4 (4.9) |
| 2 | R3 | **Nueva, historia 38** «¿`ORCA_PANE_KEY` es credencial?»: confirmar primero; si no lo es, lista corta de excepciones por nombre y caso nuevo de «no se reporta» en el oráculo; si lo es, cerrar sin cambios. | Épica 3 (3.12) |
| 3 | R4 | **Nueva, historia 39** «Caja de efecto sin vacío»: frase fija del catálogo cuando el proveedor es `no_aplica`; TH-10 aclara que la falta de sandbox es de la plataforma; TH-14 sigue sin mostrar el comando. | Épica 6 (6.9) |
| 4 | R8 | **Nueva, historia 40** «Agente analizado sin señales de configuración»: verificar el caso en el código; si se confirma, frase fija en el reporte y regla nueva en FR-31; y explicar «regla sin origen verificado». | Épica 6 (6.10) |
| 5 | R5 | **Evidencia agregada a la Story 7.6 (`--redact-paths`) y a la pregunta 9 del PRD**, en lugar de una historia nueva: la épica 7 ya tenía esa historia, bloqueada por tu decisión. Se deja como candidato de diseño el modo «para compartir» (encabezado como `~/…`, archivos no revisados agrupados por motivo y cantidad, caso nuevo en la prueba canario). *Corregido al aplicar: la propuesta original hablaba de una «historia 41», que duplicaba la 7.6.* | Épica 7 (7.6) |
| 6 | R6 | **Ampliada, historia 35 (Story 6.7):** se agrega que `<html lang>` y `<title>` sigan el idioma elegido y que «hook», «sandbox» y «Route map» tengan equivalente o se expliquen. Se prueba con un reporte en español. | Épica 6 (6.7) |

### PRD

| # | Origen | Cambio |
|---|---|---|
| 7 | R1 | §7.2, Fase 2: nueva línea «Modelar `hooks.PreToolUse` de Claude Code para refinar el nivel. Evidencia: corrida real del 2026-11-11, 4 hallazgos de Claude Code en Potencial por este motivo. No subiría los TH-1 reconocidos por nombre (AD-11).» |
| 8 | R8 | FR-31: regla nueva **condicionada** a que la historia 40 confirme el caso. Hoy no se redacta. |

### Documentación

| # | Origen | Cambio |
|---|---|---|
| 9 | R7 | `deferred-work.md`: dos preguntas a verificar con el segundo proyecto de prueba: (a) ¿«No se pudo revisar» debe poder filtrarse en la UI o basta la sección de limitaciones?; (b) ¿la evidencia de «configurados» se trunca sin avisar? |
| 10 | R1 a R8 | `research.md`: corregir la atribución de los 0 Comprobados (ver §1). |

### Seguimiento de la sprint (`implementation-artifacts/sprint-status.yaml`)

Agregado en `backlog` el 2026-11-11, tras tu aprobación: `3-12` (historia 38), `4-9` (37), `6-9` (39) y `6-10` (40). `6-7` quedó marcada como «ampliada» y `7-6` con la evidencia nueva.

## 5. Clasificación y entrega

**Alcance: moderado.** Reordena el backlog (4 historias nuevas, 1 ampliada y 1 con evidencia nueva) sin cambiar el MVP ni la arquitectura.

| Rol | Responsabilidad |
|---|---|
| **Alex (dueño del producto)** | Aprobar esta propuesta; confirmar si `ORCA_PANE_KEY` es una credencial (historia 38). |
| **John (PM)** | Aplicar los cambios 7 y 8 al PRD; ordenar las historias 37 a 41 respecto de 34 a 36. |
| **Amelia (desarrollo)** | Escribir las fichas de las historias 37 a 41 y la ampliación de la 35; implementarlas una a una. |
| **Sally (UX)** | Revisar `EXPERIENCE.md` para la marca «también en», la caja de efecto y el modo para compartir. |
| **Winston (arquitectura)** | Sin tarea, salvo revisar la historia 40 si cambia FR-31. |

**Criterios de éxito:**
- Las 5 historias nuevas quedan en `epics.md` y `sprint-status.yaml`.
- Una nueva corrida sobre el mismo proyecto no muestra el trío de `.env` como ruido duplicado, ni cajas vacías, ni `lang` distinto del idioma elegido.
- Ninguna prueba de las reglas no negociables ni del oráculo cambia de resultado, salvo el caso nuevo de la historia 38.
- Se vuelve a escanear alrededor del **2026-12-11** con la versión vigente y se compara con este reporte.

## 6. Historial de decisiones

| Propuesta | Decisión de Alex |
|---|---|
| R1 hooks | Aprobada |
| R2 repetidos | Aprobada |
| R3 ORCA | Aprobada |
| R4 efecto vacío | Aprobada |
| R5 compartir | Aprobada |
| R6 idioma | Aprobada |
| R7 verificar | Aprobada |
| R8 opencode | Aprobada |
