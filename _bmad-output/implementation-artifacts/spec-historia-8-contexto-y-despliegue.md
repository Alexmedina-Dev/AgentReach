---
title: 'Historia 8. Archivos de contexto (también fuera del proyecto) y scripts de despliegue'
type: 'feature'
created: '2026-11-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['{project-root}/_bmad-output/planning-artifacts/historias-mvp.md']
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problema:** AgentReach no marca archivos de contexto del agente con instrucciones sospechosas, scripts de despliegue, ni archivos de instrucciones sueltos en la carpeta personal.

**Enfoque:** tres detectores. `DetectorContexto` (TH-5) lee `CLAUDE.md` y `AGENTS.md` con la lectura segura y reporta cuando coinciden al menos dos grupos de patrones simples (anular reglas, leer un secreto, enviar a una URL, ocultarlo), sin copiar el texto. `DetectorDespliegue` (TH-9) reconoce `deploy*.sh/.ps1/.bat/.cmd` solo por nombre. `DetectorInstruccionesFuera` (TH-13) mira solo la existencia y el tipo de `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` y `.cursorrules` en el home y en Descargas, Escritorio y Documentos, solo con el opt-in de la Historia 5.

## Boundaries & Constraints

**Always:** el texto sospechoso nunca sale; los scripts de despliegue no se leen; los archivos de TH-13 no se abren ni se enumeran las carpetas; con el opt-in apagado no se toca el disco; nivel provisional hipótesis; lo no leído sale como `NoRevisado`.

**Never:** análisis profundo de intención; leer scripts; saber desde qué carpeta se lanzó el agente; que un archivo del proyecto active el opt-in.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CX-02 | AGENTS.md con instrucción sospechosa | TH-5 con su línea, sin texto | — |
| CX-01 / NO-04 | CLAUDE.md inofensivo / deploy.yml | nada | — |
| Un solo patrón | "ignora las instrucciones" suelto | nada | — |
| AGENTS.md de 5 MB+1 o no UTF-8 | archivo ilegible | `NoRevisado`, no "sin patrones" | — |
| deploy.sh / deploy.ps1 | scripts | TH-9 sin abrirlos | — |
| AT-03 / AT-10 | home-falso con opt-in | TH-13 solo nombre y ruta | — |
| Opt-in apagado | home-falso | nada y 4 NoRevisado, sin tocar disco | — |

</intent-contract>

## Code Map

- `src/agentreach/collectors/contexto.py`, `despliegue.py`, `instrucciones_fuera.py`.
- `src/agentreach/app/auditar.py` -- registro (tres líneas).
- Proyecto de prueba: `proyecto/AGENTS.md` (CX-02), `proyecto/CLAUDE.md` (CX-01), `.github/workflows/deploy.yml` (NO-04), `home-falso/AGENTS.md` y `home-falso/Downloads/AGENTS.md`.

## Tasks & Acceptance

**Execution:**
- `tests/test_contexto_deploy.py` -- primero
- los tres detectores y el registro

**Acceptance Criteria:**
- Given (a)-(f) de la historia, when se ejecutan, then se cumplen.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~27 findings (ciega 11, casos limite 15 mas 1 de afirmacion) - high 0, medium 7, low 6, false 1, maybe-false 0
- `[medium]` `[patch]` con el opt-in apagado solo se informaban 4 de las 7 carpetas (faltaban Descargas, Escritorio, Documentos) - ahora las siete
- `[medium]` `[patch]` caracteres de ancho cero dentro de una palabra evadian los patrones - se descartan los caracteres de formato (categoria Cf)
- `[medium]` `[patch]` instrucciones partidas en varias lineas evadian la deteccion - ventana de 3 lineas, citando la linea exacta cuando cabe en una
- `[medium]` `[patch]` expresiones sin frontera de palabra (casino digas, sin que usuarios) - fronteras anadidas
- `[medium]` `[patch]` una carpeta, enlace o tuberia llamada deploy.sh se reportaba como script; las carpetas no recorridas parecian "sin scripts" - se exige archivo regular y se propagan los NoRevisado del recorrido
- `[low]` `[patch]` motivo nulo en NoRevisado; linea enorme sin tope (4000 caracteres); home que no es carpeta; GEMINI.md y .cursorrules en el proyecto (misma lista que TH-13, sin duplicarla)
- `[low]` `[defer]` ReDoS con expresiones mas complejas no probado mas alla de una linea de 2 MB; otros idiomas, homoglifos y texto codificado; nombres de despliegue .py/.js o sin extension; nombres exactos en sistemas que distinguen mayusculas
- `[false]` archivo reportado por ruta real fuera del proyecto - el recorrido no lista enlaces entre los archivos
- `[reject]` recorridos repetidos por cada detector (costo conocido, historia de rendimiento posterior), pruebas del proyecto de prueba que se omiten sin la variable, TOCTOU entre carpeta y archivo

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorContexto` (TH-5, dos grupos de patrones simples), `DetectorDespliegue` (TH-9, solo por nombre) y `DetectorInstruccionesFuera` (TH-13, solo con opt-in y solo metadatos), registrados en la ejecucion de punta a punta.
Archivos: `collectors/contexto.py`, `collectors/despliegue.py`, `collectors/instrucciones_fuera.py`, `app/auditar.py`, `tests/test_contexto_deploy.py`, `tests/test_primera_ejecucion.py`.
Verificacion: con el proyecto de prueba 415 pasan, 11 omitidas; sin el 389 pasan, 37 omitidas. Ruff limpio. CX-02 se detecta (AGENTS.md:4); CX-01 y NO-04 no; AT-03 y AT-10 solo con el opt-in.
Sin commit. Riesgo residual: los `defer`.
