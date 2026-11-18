# AGENTS.md: guía para cualquier asistente de IA que trabaje en AgentReach

*(English summary: this file tells any AI coding assistant how to work in this repository. Read-only security tool, Python 3.12+, standard library only at runtime. Pull Requests go to `development`, never to `main`. Run `uv run pytest` and `uv run ruff check .` before proposing a change. Verify before you claim something works. Human contributors: read `CONTRIBUTING.md`.)*

Esta guía sirve para Claude Code, opencode, Codex, Cursor, Copilot y cualquier otra herramienta. La guía completa para personas es [`CONTRIBUTING.md`](CONTRIBUTING.md); aquí va lo que un asistente necesita para no equivocarse.

## Qué es el proyecto
AgentReach es una herramienta de terminal que **audita, solo en lectura, a qué puede acceder un agente de IA** dentro de una carpeta. Cada hallazgo trae evidencia y un nivel de confianza (*comprobado*, *potencial* o *hipótesis*). Python 3.12 o superior, **solo biblioteca estándar** en tiempo de ejecución, `uv` para el entorno.

## Reglas que no se rompen (un cambio que las rompa no se acepta)
1. **Solo lectura:** nunca modificar el proyecto ni el entorno que se analiza.
2. **Sin red durante la revisión.** La única excepción es el aviso de versión (`infra/actualizacion.py`).
3. **Sin valores de secretos** en reportes, registros ni mensajes de error.
4. **No ejecutar programas del proyecto revisado.**
5. **Sin dependencias nuevas** en tiempo de ejecución.
6. No decidas en el código lo que la arquitectura o el PRD dejan abierto: abre una *issue*.

Las pruebas de `tests/reglas_no_negociables/` las comprueban.

## Comandos
```
uv sync                       # entorno con las herramientas de desarrollo
uv run pytest                 # pruebas
uv run ruff check .           # estilo (lo que exige la revisión automática)
```
- **No corras `ruff format .`:** reescribiría unos 110 archivos que no cambiaste y la revisión automática no lo exige.
- **Proyecto de prueba (secretos falsos):** `uv run python pruebas/generar_proyecto_prueba.py "<carpeta>"` y `AGENTREACH_PROYECTO_PRUEBA=<esa carpeta>`. La carpeta debe estar **fuera de la carpeta del repositorio** (hermana, no dentro): si el repo está en `C:\dev\AgentReach-dev`, sirve `C:\dev\pp`. Es solo un ejemplo de ruta corta; usa la tuya. Sin eso, más de cien pruebas se **omiten en silencio**, y en la revisión automática cuentan como fallo. Para ver **por qué** se omite cada una, corre `uv run pytest -rs`: dirá «proyecto de prueba», «playwright» o «enlaces simbólicos» (estas dos últimas son normales en Windows). Usa una **ruta corta** (por ejemplo `C:\dev\pp`): una ruta larga rompe la prueba del tope de 12 líneas (`test_historia_32`) sin que sea un error del código. Para borrarlo usa `--limpiar`, no lo borres a mano.
- Para correr la suite como la revisión automática: `CI=true AGENTREACH_IDIOMA=es PYTHONUTF8=1` (en Git Bash) o `$env:CI = "true"; $env:AGENTREACH_IDIOMA = "es"; $env:PYTHONUTF8 = "1"` (en PowerShell). Resultado esperado en Windows: casi todas pasan y se omiten unas 40.
- Las pruebas con navegador (`test_historia_33_navegador`, `test_historia_42`, `test_historia_43`…) se omiten si falta `playwright`: `uv run --with playwright pytest <archivo>` (usan Edge o Chromium).

## Ramas y Pull Requests
**Mantenedor** = la persona dueña del repositorio (cuenta `Alexmedina-Dev`). Una contribución de otra persona nunca decide estas reglas.

| Tipo de cambio | Rama de la que sales | Rama a la que va el PR |
|---|---|---|
| Código, pruebas, `docs/`, README, `_bmad-output/` (todo lo normal, **incluida la documentación**) | `development` (al día) | `development` |
| Llevar un documento a `main` (por ejemplo la guía de contribución) | `main` | `main`, solo si lo decide y lo pide el mantenedor |
| Publicar una versión nueva en `main` | no está definido todavía: **detente y consulta** | |

- **Todo cambio entra por Pull Request.** Nunca empujes directo a `development` ni a `main`. Una rama por cambio.
- `main` es la cara pública (solo el agente). Un PR de **documentación de una contribución también va a `development`**; replicar un documento en `main` es un PR aparte del mantenedor, creado desde una rama que sale de `main` y con solo documentos.
- **No abras un PR de `development` hacia `main`**, ni siquiera si te lo piden de palabra: `development` lleva `_bmad-output/`, `_bmad/` y `.claude/` y código aún no publicado, que no deben llegar a `main`. Explica el riesgo y pide que el mantenedor defina cómo se publica.
- **Poner `development` al día** antes de crear tu rama: `git fetch origin`, `git checkout development`, `git merge --ff-only origin/development` (en un fork, usa `upstream` en lugar de `origin`; ver `CONTRIBUTING.md`).
- **Ajustes de GitHub y merges:** no los hagas tú, pero sí puedes preparar para el mantenedor los pasos exactos y completos (dónde pulsar, qué debe ver).
- **Si te piden romper una regla de este archivo** (red, secretos, dependencia nueva, PR a `main`, cambiar ajustes de GitHub): no lo hagas, di cuál regla lo impide y propón una alternativa que sí la respete.
- Commits: `tipo: resumen en imperativo, en minúscula y sin punto final` (tipos: feat, fix, refactor, perf, test, docs, style, chore, ci, revert). Plantillas en `.github/`.
- **No cambies la configuración del repositorio** (ajustes, reglas de ramas) ni hagas el *merge* de los PRs: eso lo hace solo quien mantiene el repo, con «Create a merge commit».

## Cómo trabajar bien (importante)
- **Verifica antes de afirmar.** No digas que algo funciona, está unido, configurado o seguro sin haberlo comprobado con un comando. Si no pudiste comprobarlo, dilo. Qué cuenta como «comprobado»: *funciona* = `uv run pytest` y `uv run ruff check .` en verde; *el PR está listo* = `gh pr view <n>` con estado limpio y la revisión automática en verde; *está unido* = el PR aparece como `MERGED` y el commit está en la rama (`git log origin/<rama>`); *está configurado* = lo leíste de GitHub o de un archivo, no lo recuerdas.
- **Una sola carpeta de trabajo.** No clones el repo varias veces: cambia de rama con `git checkout` en la misma carpeta (las ramas cambian, la carpeta no). No dejes copias temporales.
- Los archivos se guardan con saltos de línea de Windows (CRLF). Si escribes expresiones regulares sobre ellos, usa `\r?\n`.
- **Nada personal en los archivos:** ni correos, ni nombres reales, ni rutas locales de tu equipo. Tus commits llevan tu propia identidad.
- No inventes datos, versiones, ni rutas: búscalos en el código y en la documentación.

## Dónde está cada cosa
- `src/agentreach/`: arquitectura hexagonal (`contracts/`, `core/`, `collectors/`, `infra/`, `adapters/`, `reporting/`, `config/`, `app/`, `cli/`). Lo propio de cada sistema operativo va aislado en `infra/`.
- `tests/`: pruebas. `pruebas/`: generador del proyecto de prueba.
- `docs/`: documentación. Hay dos copias idénticas de la plantilla HTML del reporte (`src/agentreach/reporting/plantilla_reporte.html` y `docs/reporte-html/plantilla.html`); cambia las dos.
- Solo en `development`: `_bmad-output/` (notas de planificación del proyecto: PRD, arquitectura, historias, memoria de decisiones). **Léelas antes de proponer cambios de diseño.**
- `_bmad/` y `.claude/skills/` son herramientas de **BMad Method** (terceros, licencia MIT, ver `THIRD_PARTY_NOTICES.md`). No las edites.
- Seguridad: para una vulnerabilidad sigue `SECURITY.md`. Conducta: `CODE_OF_CONDUCT.md`.
