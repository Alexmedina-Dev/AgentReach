# Cómo contribuir a AgentReach

AgentReach es una herramienta de código abierto que **audita a qué puede acceder un agente de IA** en tu entorno (archivos, variables de entorno, credenciales, etc.), con evidencias y niveles de confianza. El MVP (producto mínimo viable) ya está construido y en pruebas con agentes reales: puedes instalarlo y usarlo (ver `README.md`).

Para el contexto completo lee `README.md`. En la rama `development` (la tuya, ver abajo) están la arquitectura vigente, en `_bmad-output/planning-artifacts/architecture/architecture-agent-reach-2026-11-11/ARCHITECTURE-SPINE.md`, y las historias del producto, en `_bmad-output/planning-artifacts/historias-mvp.md`.

Este proyecto sigue un [código de conducta](CODE_OF_CONDUCT.es.md) (versión en inglés: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)). Al participar te comprometes a respetarlo.

## Dónde empezar y qué esperar

- **Aportes bienvenidos:** reportes de errores, ideas, revisión del diseño, casos de prueba (por ejemplo, patrones de exposición bien documentados) y correcciones pequeñas de código.
- **Por dónde entrar:** busca las *issues* con la etiqueta [`good first issue`](https://github.com/Alexmedina-Dev/AgentReach/labels/good%20first%20issue) o [`help wanted`](https://github.com/Alexmedina-Dev/AgentReach/labels/help%20wanted). Si aún no hay ninguna que te sirva, abre una *issue* contando qué quieres hacer **antes** de empezar un cambio grande. Si tomas una issue existente, comenta en ella que la tomas antes de programar, para que nadie la repita.
- **Tiempos:** quien mantiene el repositorio revisa los Pull Requests cuando puede; no hay un plazo garantizado.
- **Licencia de tu aporte:** al enviar un Pull Request, tu aporte se publica bajo la licencia Apache-2.0 del proyecto (sección 5 de la licencia).
- **Sistemas:** hoy el proyecto se prueba solo en Windows (la revisión automática corre en Windows). Si usas macOS o Linux, tu aporte es bienvenido: dilo en el Pull Request, porque las pruebas pueden comportarse distinto.
- **Tu correo:** tus commits llevan tu nombre y el correo que tengas configurado en git, y este repositorio es público. Si no quieres que se vea tu correo, usa el correo anónimo que GitHub te da (Settings → Emails).

## Preparar el entorno

Necesitas [uv](https://docs.astral.sh/uv/) (gestor de paquetes y entornos de Python). No hace falta instalar Python aparte: uv descarga la versión 3.12 o superior que el proyecto pide.

### Si no mantienes el repositorio (lo normal)

No puedes subir ramas al repositorio original, así que trabajas en una copia propia (*fork*):

1. En GitHub, pulsa **Fork** en la página del repositorio. Eso crea tu copia.
2. Clona **tu copia**, en la rama `development`, y crea una rama para tu cambio:

```powershell
git clone -b development https://github.com/<tu-usuario>/AgentReach.git
cd AgentReach
git checkout -b mi-cambio    # una rama por cambio; nunca trabajes directo en development
uv sync                      # crea .venv e instala las dependencias de desarrollo
uv run agentreach --version  # comprueba que la CLI (interfaz de línea de comandos) funciona
```

3. Haz tu cambio, corre las pruebas (ver abajo) y súbelo a tu copia: `git push origin mi-cambio`.
4. En GitHub, abre un **Pull Request** desde tu rama hacia la rama **`development`** del repositorio original (nunca hacia `main`).

### Si mantienes el repositorio

Clonas directamente el repositorio original, creas una rama desde `development` y abres el Pull Request hacia `development`:

```powershell
git clone -b development https://github.com/Alexmedina-Dev/AgentReach.git
cd AgentReach
git checkout -b mi-cambio
```

Tengas el permiso que tengas, **trabaja en una sola carpeta**: las ramas cambian, la carpeta no.

### Mantén tu copia al día antes de empezar y antes de abrir el Pull Request

`development` cambia cada vez que se une un Pull Request. Si tu copia se queda atrás, tu Pull Request puede **chocar** con cambios nuevos o deshacerlos sin querer. Por eso, **siempre trae lo nuevo de `development` antes de crear tu rama y otra vez antes de abrir el Pull Request**:

```powershell
# Una sola vez: registra el repositorio original con el nombre "upstream"
# (solo si trabajas desde tu fork; quien mantiene el repo ya lo tiene como "origin")
git remote add upstream https://github.com/Alexmedina-Dev/AgentReach.git

# Antes de crear tu rama: pon tu development al día
git checkout development
git fetch upstream
git merge --ff-only upstream/development   # quien mantiene el repo usa: git pull --ff-only origin development
git checkout -b mi-cambio

# Antes de abrir el Pull Request: trae lo nuevo a tu rama y vuelve a correr las pruebas
git fetch upstream
git rebase upstream/development            # quien mantiene el repo usa: git rebase origin/development
uv run pytest
git push --force-with-lease origin mi-cambio
```

- Si `git rebase` marca un **conflicto**, git te dice qué archivos chocan. Arréglalos, usa `git add <archivo>` y `git rebase --continue`. Si te pierdes, `git rebase --abort` deja todo como estaba.
- Tu fork en GitHub también tiene un botón **Sync fork** que hace lo mismo para tu `development`.
- Aunque tengas el permiso, **nunca subas directo a `development` ni a `main`**: todo cambio entra por Pull Request. GitHub lo exige.

Tengas el permiso que tengas, **trabaja en una sola carpeta**: las ramas cambian, la carpeta no.

## Correr las pruebas y el estilo

**Inicio rápido, en orden** (la primera vez, en PowerShell; la suite completa tarda unos 3 minutos):

```powershell
uv sync                                                        # 1. el entorno
uv run python pruebas/generar_proyecto_prueba.py "C:\dev\pp"   # 2. el proyecto de prueba (fuera del repo, con ruta corta)
$env:AGENTREACH_PROYECTO_PRUEBA = "C:\dev\pp"                  # 3. dile a las pruebas dónde está
$env:AGENTREACH_IDIOMA = "es"; $env:PYTHONUTF8 = "1"           # 4. mensajes en español y UTF-8
uv run pytest                                                  # 5. las pruebas
uv run ruff check .                                            # 6. el estilo
```

En Git Bash es lo mismo, con `export` en lugar de `$env:` (por ejemplo `export AGENTREACH_PROYECTO_PRUEBA='C:\dev\pp'`).

**Resultado esperado en Windows**, sin modo desarrollador y sin `playwright`: pasan casi todas (unas 1900) y se omiten unas 40 (enlaces simbólicos, navegador y pruebas solo para POSIX). Un fallo es real: corrígelo antes de abrir el Pull Request. Para reproducir exactamente la revisión automática de GitHub añade `$env:CI = "true"`: así las pruebas que se omitirían por falta del proyecto de prueba cuentan como fallo.

Estos son los mismos comandos con más detalle:

```powershell
uv run pytest        # pruebas
uv run ruff check .  # revisión de estilo
# No corras «ruff format .»: hoy reescribiría ~110 archivos que no cambiaste, y la revisión automática no lo exige.
```

Las pruebas de `tests/reglas_no_negociables/` comprueban las reglas de abajo (solo lectura, sin red, sin ejecutar programas y sin valores de secretos). Un cambio que haga fallar una de ellas no se acepta.

### El proyecto de prueba (secretos falsos)

Varias pruebas, entre ellas todas las de reglas no negociables y las del oráculo, auditan un **proyecto de prueba**: una carpeta con secretos **falsos** que genera `pruebas/generar_proyecto_prueba.py`. Esa carpeta **no se sube al repositorio** y debe estar **fuera** de él (el generador se niega a crearla dentro, o en OneDrive).

```powershell
# 1. Genera el proyecto de prueba en una carpeta fuera del repositorio
uv run python pruebas/generar_proyecto_prueba.py "C:\dev\pp"

# 2. Dile a las pruebas dónde está
$env:AGENTREACH_PROYECTO_PRUEBA = "C:\dev\pp"

# 3. Corre las pruebas
uv run pytest
```

- **Sin la variable `AGENTREACH_PROYECTO_PRUEBA`, más de cien pruebas se omiten** (*skipped*) en silencio. En GitHub, la revisión automática (CI) las trata como fallos, así que conviene correrlas con el proyecto de prueba antes de abrir tu Pull Request.
- **Usa una ruta corta** (como `C:\dev\pp`): una ruta larga rompe la prueba del tope de 12 líneas (`test_historia_32`) aunque tu código esté bien.
- Si tu Windows no permite enlaces simbólicos, el generador imprime `symlink: no creado - OSError: [WinError 1314]`. Es lo esperado, no un error.
- Las pruebas con navegador (reporte HTML) se omiten si falta `playwright`; la revisión automática de GitHub tampoco las corre. Para correrlas tú: `uv run --with playwright pytest tests/test_historia_42.py` (usan Edge o Chromium).
- Las pruebas esperan los mensajes en español. Si tu sistema está en otro idioma, usa también `$env:AGENTREACH_IDIOMA = "es"` y `$env:PYTHONUTF8 = "1"`, como hace `.github/workflows/ci.yml`.
- Las pruebas de enlaces simbólicos se omiten en Windows si tu usuario no puede crearlos (hace falta el modo desarrollador o ser administrador). GitHub sí las corre.
- Para quitar el proyecto de prueba usa `uv run python pruebas/generar_proyecto_prueba.py --limpiar "<carpeta>"`. Bórralo así y no a mano: el generador deja algunos archivos con permisos negados a propósito.

## Reglas no negociables

Todo cambio debe respetarlas. Si un cambio las rompe, no se acepta.

1. **Solo lectura.** AgentReach nunca modifica el proyecto ni el entorno que analiza. No se abren archivos para "probar" permisos. (PRD, FR-1) Fuera de lo analizado solo escribe `--salida` y la carpeta `AgentReach-reportes` de la carpeta personal; durante la revisión no lanza programas, y al terminar solo abre el reporte HTML en el navegador si la persona lo permitió. (Historia 21)
2. **Sin red durante la revisión.** Ninguna conexión de red salvo la consulta del número de versión (Historia 31): solo al abrir, cada 15 días como máximo, en `infra/actualizacion.py`. No se añaden dependencias que usen red. (PRD, FR-2)
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
| `development` | Aquí llegan los aportes de contribuyentes y se hacen todos los cambios. **Tu Pull Request apunta a esta rama.** También tiene las notas de planificación del proyecto (`_bmad-output/`). |
| `PruebaAlex` | Archivo de la etapa anterior del proyecto. Ya no se usa: no se contribuye ahí. |

- Crea tu rama desde `development` y abre el Pull Request hacia `development`, nunca hacia `main`.
- **Nombre de la rama:** corto y que diga qué haces; puedes usar el tipo del commit como prefijo (`fix/ignorar-venv`, `docs/mejorar-guia`). No hay un formato obligatorio.
- La plantilla `.github/pull_request_template.md` se llena sola con `bmad-create-pr` si usas BMAD; si no, llénala a mano. Antes de abrir el PR corre `uv run pytest` y `uv run ruff check .`: la revisión automática hace lo mismo y debe quedar en verde.
- Las ramas protegidas y su configuración las gestiona solo la persona dueña del repositorio.
- Mensajes de commit según `.github/commit_template.md`: `tipo: resumen en imperativo, en minúscula y sin punto final`.
  Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `revert`.
- Un commit = un cambio con sentido, con sus pruebas y documentación.
- **Versiones:** al lanzar se sube el tercer número (`0.1.0` → `0.1.1` → `0.1.2`) en `pyproject.toml`. El aviso de versión compara esos tres números con los de `main`.
- Las historias se hacen de una en una: una rama desde `development` y un Pull Request por historia.

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
