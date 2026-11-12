# Guía de BMAD  — aplicada a AgentReach

> Basada en BMAD 6.12.4 instalado en este proyecto (catálogo en `_bmad/_config/bmad-help.csv`).
> Objetivo: aprender el proceso paso a paso. Si algo difiere de lo que ves, `bmad-help` es la fuente de verdad.

## 1. La idea central

BMAD no es un programa que corre solo: es un conjunto de **skills** (flujos de trabajo guiados) y **agentes** (personas con un rol) que usas desde Claude Code. Tú decides, ellos te hacen preguntas, redactan documentos y construyen.

**Regla de oro:** cada fase produce un documento, y la siguiente fase lo usa como insumo. Se va de lo difuso (idea) a lo concreto (código):

```
Idea → Brief → PRD → (UX) → Arquitectura → Épicas e Historias → Sprint → Build → Review
```

## 2. Preparación (una sola vez)

1. Instalar `uv` (BMAD lo necesita para algunos scripts):
 `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Abrir Claude Code **dentro de la carpeta `agent-reach`** (si no, no carga las skills de BMAD).
3. Probar con `/bmad-help`.

## 3. Cómo se invoca todo

Hay dos formas, y conviene entender la diferencia:


| Forma                        | Ejemplo                                  | Qué es                                                                        |
| ---------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------- |
| **Skill (flujo de trabajo)** | `/bmad-product-brief`                    | Ejecuta un proceso concreto y genera un documento.                            |
| **Agente (persona)**         | "habla con Mary" o `/bmad-agent-analyst` | Abre una conversación con un rol; desde su menú lanzas los flujos de ese rol. |


Los agentes instalados:


| Agente          | Nombre  | Rol                                    | Skill                    |
| --------------- | ------- | -------------------------------------- | ------------------------ |
| Analista        | Mary    | Investigación, competencia, requisitos | `bmad-agent-analyst`     |
| Product Manager | John    | PRD y descubrimiento de requisitos     | `bmad-agent-pm`          |
| Arquitecto      | Winston | Diseño técnico                         | `bmad-agent-architect`   |
| Desarrolladora  | Amelia  | Implementa historias y código          | `bmad-agent-dev`         |
| Diseñadora UX   | Sally   | UX/UI                                  | `bmad-agent-ux-designer` |


Para empezar no necesitas memorizar nada: **invoca la skill de cada paso** y, si te pierdes, `/bmad-help`.

## 4. El proceso, paso a paso

### Fase 0 — Orientarse (opcional pero recomendada para aprender)


| Paso            | Skill                 | Para qué                                                                          |
| --------------- | --------------------- | --------------------------------------------------------------------------------- |
| Ayuda           | `/bmad-help`          | Dice en qué punto estás y qué sigue. Úsala siempre que dudes.                     |
| Probar la idea  | `/bmad-forge-idea`    | Personas que cuestionan tu idea hasta endurecerla.                                |
| Investigar      | `/bmad-deep-recon`    | Investigación (competitiva, técnica…). Útil aquí: revisar AgentSec, Bulwark, etc. |
| Lluvia de ideas | `/bmad-brainstorming` | Si quieres explorar variantes.                                                    |


### Fase 1 — Planear: qué construir

1. **Product Brief** — `/bmad-product-brief`
 Conversación guiada que captura la idea en un resumen corto. Dale `CONTEXTO-PROYECTO.md` como insumo.
 *Alternativa más exigente:* `/bmad-prfaq` (método "Working Backwards" de Amazon: escribes primero el comunicado de prensa del producto terminado).
2. **PRD** (Documento de Requisitos) — `/bmad-prd`
 Requisitos, alcance del MVP, casos de uso. **Es un paso obligatorio.** Aquí se resuelven las "preguntas abiertas" de la sección 11 de `CONTEXTO-PROYECTO.md`. También sirve para actualizarlo y validarlo.
3. **UX** — `/bmad-ux` *(opcional)*
 Para AgentReach, que es un CLI, probablemente baste con definir cómo se ve el reporte. Puedes omitirlo.

### Fase 2 — Diseñar: cómo construirlo

4. **Arquitectura** — `/bmad-architecture` *(obligatorio)*
 Registra las decisiones técnicas (módulos, modelo de hallazgos, cómo se calcula el AES, Windows vs POSIX) para que las historias sean consistentes entre sí.
5. **Épicas e historias** — `/bmad-create-epics-and-stories` *(obligatorio)*
 Divide el PRD y la arquitectura en trozos construibles, con criterios de aceptación.
6. **Sprint planning** — `/bmad-sprint-planning` *(obligatorio)*
 Verifica que lo planeado esté completo (resultado PASS / CONCERNS / FAIL) y genera el archivo de estado que seguirán los agentes de implementación.

### Fase 3 — Construir

7. **Build** — `/bmad-build`
 El flujo estándar: aclara la intención, planifica, implementa, revisa y presenta. Se hace **historia por historia**.
 *Requiere `uv`.*
8. **Revisión** (opcionales)
   - `/bmad-code-review`: revisión extra con varios revisores en paralelo.
   - `/bmad-walkthrough`: te explica un cambio para que lo revises tú.
   - `/bmad-qa-generate-e2e-tests`: genera pruebas automatizadas.
   - `/bmad-review`: revisa cualquier cosa (código, PRD, arquitectura, texto).
9. **Retrospectiva** — `/bmad-retrospective` *(opcional, al cerrar una épica)*
 Qué salió bien, qué no, y qué cambiar.

## 5. Herramientas que se usan en cualquier momento


| Skill                        | Cuándo                                                                                                                              |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `/bmad-advanced-elicitation` | Al terminar un borrador: pre-mortem, primeros principios, red team, método socrático. **Muy buena para aprender**: aplícala al PRD. |
| `/bmad-party-mode`           | Varios agentes discuten tu decisión (por ejemplo Winston y John debatiendo una opción de diseño).                                   |
| `/bmad-correct-course`       | Cambió algo grande a mitad del trabajo: evalúa el impacto en PRD, épicas y arquitectura.                                            |
| `/bmad-spec`                 | Condensa cualquier insumo en un `SPEC.md` corto.                                                                                    |
| `/bmad-project-context`      | Crea el bloque de instrucciones para agentes (`AGENTS.md`) del repo, cuando ya haya código.                                         |
| `/bmad-customize`            | Cambiar cómo se comporta un agente o flujo, sin editar TOML a mano.                                                                 |


## 6. Ruta recomendada para tu primer recorrido

1. `/bmad-help`: mira qué te sugiere.
2. `/bmad-product-brief`: usa `CONTEXTO-PROYECTO.md`.
3. `/bmad-deep-recon` (tipo `competitive`): revisa AgentSec, Bulwark y las demás herramientas.
4. `/bmad-prd`: define el MVP.
5. `/bmad-advanced-elicitation`: pásalo por un *pre-mortem*.
6. `/bmad-architecture`.
7. `/bmad-create-epics-and-stories`.
8. `/bmad-sprint-planning`.
9. `/bmad-build`: la primera historia. Aquí empieza el código.
10. `/bmad-code-review` y `/bmad-walkthrough`: revisa lo construido.

## 7. Dónde quedan los documentos

- `_bmad-output/`: carpeta de salida por defecto. Dentro hay subcarpetas para planificación (brief, PRD, arquitectura, épicas) e implementación (estado del sprint, specs).
- `_bmad/`: la instalación de BMAD. No la edites a mano; las personalizaciones van en `_bmad/custom/` (usa `/bmad-customize`).
- `.claude/skills/`: las skills que ve Claude Code.

## 8. Consejos para aprender

- **Lee lo que genera cada fase antes de seguir.** Si el brief está mal, el PRD y todo lo demás heredan el error.
- **Un contexto por fase:** conviene empezar una conversación nueva para cada fase grande (brief, PRD, arquitectura, build). Los documentos son la memoria, no el chat.
- **No saltes los pasos obligatorios** (PRD, Arquitectura, Épicas, Sprint planning).
- **Cuestiona al agente.** Si una decisión no te convence, pídele alternativas o usa `/bmad-party-mode`.
- **Si cambias de idea a mitad de camino**, usa `/bmad-correct-course` en vez de editar documentos sueltos.
- **Esta guía puede quedar desactualizada.** Documentación oficial: [https://docs.bmad-method.org/](https://docs.bmad-method.org/)

## 9. Problemas frecuentes


| Síntoma                                | Causa probable                                                           |
| -------------------------------------- | ------------------------------------------------------------------------ |
| Las skills `/bmad-...` no aparecen     | Claude Code no se abrió dentro de `agent-reach`.                         |
| `bmad-build` se detiene al activarse   | Falta `uv`.                                                              |
| No sabes qué sigue                     | `/bmad-help`.                                                            |
| El documento no refleja lo que querías | Aplica `/bmad-advanced-elicitation` o repite el paso con mejor contexto. |
