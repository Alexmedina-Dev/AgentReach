# Cómo contribuir a AgentReach

AgentReach es una herramienta de código abierto que **audita a qué puede acceder un agente de IA** en tu entorno (archivos, variables de entorno, credenciales, etc.), con evidencias y niveles de confianza. El MVP (producto mínimo viable) ya está construido y en pruebas con agentes reales: puedes instalarlo y usarlo (ver `README.md`).

Para el contexto completo lee `README.md`. La arquitectura vigente está en `_bmad-output/planning-artifacts/architecture/architecture-agent-reach-2026-11-11/ARCHITECTURE-SPINE.md`, y las historias del producto en `_bmad-output/planning-artifacts/historias-mvp.md`.

## Preparar el entorno

Necesitas [uv](https://docs.astral.sh/uv/) (gestor de paquetes y entornos de Python). No hace falta instalar Python aparte: uv descarga la versión 3.12 o superior que el proyecto pide.

```powershell
git clone -b development https://github.com/Alexmedina-Dev/AgentReach.git
cd AgentReach
uv sync                      # crea .venv e instala las dependencias de desarrollo
uv run agentreach --version  # comprueba que la CLI (interfaz de línea de comandos) funciona
```

## Correr las pruebas y el estilo

```powershell
uv run pytest        # pruebas
uv run ruff check .  # revisión de estilo
uv run ruff format . # formato
```

Las pruebas de `tests/reglas_no_negociables/` comprueban las reglas de abajo (solo lectura, sin red, sin ejecutar programas y sin valores de secretos). Un cambio que haga fallar una de ellas no se acepta. Algunas pruebas se omiten (*skipped*) cuando dependen de otro sistema operativo.

## Reglas no negociables

Todo cambio debe respetarlas. Si un cambio las rompe, no se acepta.

1. **Solo lectura.** AgentReach nunca modifica el proyecto ni el entorno que analiza. No se abren archivos para "probar" permisos. (PRD, FR-1) Fuera de lo analizado solo escribe `--salida` y la carpeta `AgentReach-reportes` de la carpeta personal; durante la revisión no lanza programas, y al terminar solo abre el reporte HTML en el navegador si la persona lo permitió. (Historia 21)
2. **Sin red por defecto.** Ninguna conexión de red salvo que el usuario la active de forma explícita. No se añaden dependencias que usen red. (PRD, FR-2)
3. **Sin valores de secretos.** Ningún reporte, registro ni mensaje de error contiene el valor de un secreto: solo ubicación, tipo y nivel de confianza. (PRD, FR-3)
4. **Solo biblioteca estándar** de Python como dependencia en tiempo de ejecución. Las herramientas de desarrollo (pytest, ruff) van en el grupo `dev`.
5. **Niveles de confianza:** cada hallazgo es *comprobado*, *potencial* o *hipótesis*. No se afirma que algo es alcanzable solo porque exista una referencia.
6. **Lo propio de cada sistema operativo** (permisos, rutas, junctions) va aislado en `infra/`; el diseño no se ata a Windows.
7. **Decisiones abiertas:** si la arquitectura o el PRD dejan algo abierto, no lo decidas en el código. Déjalo con un comentario `TODO` que cite la decisión y abre una *issue* para consultarlo.

## Estructura

`src/agentreach/` sigue una arquitectura hexagonal (núcleo en el centro, y puertos y adaptadores a su alrededor):
`contracts/` (modelo de hallazgo y puertos), `core/`, `collectors/`, `infra/`, `adapters/`, `reporting/`, `config/`, `app/` y `cli/`. Cada paquete tiene un docstring que explica su responsabilidad.

## Ramas, commits y Pull Requests

| Rama | Para qué sirve |
|---|---|
| `main` | Lo publicable. Está protegida y no se empuja a ella directamente. |
| `development` | Aquí llegan los aportes de contribuyentes. **Tu Pull Request apunta a esta rama.** |
| `PruebaAlex` | El proyecto con sus historias, decisiones y contexto. Es la rama de trabajo de quien mantiene el repo. |

- Crea tu rama desde `development` y abre el Pull Request hacia `development`, nunca hacia `main`.
- La plantilla `.github/pull_request_template.md` se llena sola con `bmad-create-pr` si usas BMAD; si no, llénala a mano. Antes de abrir el PR corre `uv run pytest` y `uv run ruff check .`: la revisión automática hace lo mismo y debe quedar en verde.
- Las ramas protegidas y su configuración las gestiona solo la persona dueña del repositorio.
- Mensajes de commit según `.github/commit_template.md`: `tipo: resumen en imperativo, en minúscula y sin punto final`.
  Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `revert`.
- Un commit = un cambio con sentido, con sus pruebas y documentación.

## Proponer un adaptador nuevo

Un adaptador traduce las reglas y la configuración de una plataforma de agente (por ejemplo Claude Code u opencode) al modelo de hallazgo común. Cada adaptador **declara qué control real ofrece**: solo auditar, auditar y advertir, o auditar y bloquear.

1. Abre una *issue* (propuesta en GitHub) con: plataforma, versión, archivos de configuración y su precedencia, con enlaces a la documentación oficial.
2. Implementa el adaptador en su propio paquete usando solo lo que ofrece `contracts/` (nunca importes el núcleo directamente).
3. El adaptador **nunca recibe valores de secretos**: descarta los valores al leer la configuración.
4. Debe pasar el kit de conformidad (`adapters/conformance/`) y las tres pruebas de reglas no negociables.
5. Documenta la capacidad declarada y cualquier límite conocido.

El mecanismo de registro de adaptadores de terceros (puntos de entrada de Python o adaptadores dentro del árbol) está en discusión en el borrador de arquitectura (AD-2); consulta antes de empezar.

## Seguridad

Para reportar una vulnerabilidad sigue `SECURITY.md`. No publiques secretos reales en issues, pruebas ni ejemplos: los secretos de prueba se generan al ejecutar las pruebas, no se versionan.
