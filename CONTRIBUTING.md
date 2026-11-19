# Cómo contribuir a AgentReach

AgentReach es una herramienta de código abierto que **audita a qué puede acceder un agente de IA** en tu entorno (archivos, variables de entorno, credenciales, etc.), con evidencias y niveles de confianza. El MVP (producto mínimo viable) ya está construido y en pruebas con agentes reales: puedes instalarlo y usarlo (ver `README.md`).

Este proyecto sigue un [código de conducta](CODE_OF_CONDUCT.es.md) (versión en inglés: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)). Al participar te comprometes a respetarlo.

**En esta guía:**
[Antes de empezar: seguridad](#antes-de-empezar-seguridad) ·
[Dónde empezar y qué esperar](#dónde-empezar-y-qué-esperar) ·
[Preparar el entorno](#preparar-el-entorno) ·
[Correr las pruebas](#correr-las-pruebas-y-el-estilo) ·
[Reglas no negociables](#reglas-no-negociables) ·
[Ramas, commits y Pull Requests](#ramas-commits-y-pull-requests) ·
[Proponer un adaptador](#proponer-un-adaptador-nuevo) ·
[Problemas comunes](#problemas-comunes)

## Antes de empezar: seguridad

AgentReach es una herramienta de seguridad, así que **todo aporte se revisa con cuidado, venga de quien venga**:

- **Un aporte se rechaza si rompe una regla de seguridad, aunque las pruebas pasen.** En concreto: si añade conexiones de red, si ejecuta programas del proyecto que se analiza, si muestra valores de secretos o si suma dependencias nuevas. La lista completa está en [Reglas no negociables](#reglas-no-negociables).
- **Quien mantiene el repositorio lee todos los cambios** (la pestaña *Files changed* del Pull Request), no solo mira si las pruebas están en verde.
- **Si abres el Pull Request desde un fork** (tu copia, ver más abajo), la revisión automática no arranca sola: GitHub espera a que quien mantiene el repo la apruebe. Es normal y es una medida de seguridad, no un error tuyo.
- **No publiques secretos reales** (claves, contraseñas, tokens, un `.env` verdadero) en issues, pruebas, ejemplos ni commits. Los secretos de prueba son falsos y los genera el proyecto al correr las pruebas; nunca se suben al repositorio.
- Para reportar una **vulnerabilidad**, no abras una issue pública: sigue `SECURITY.md`.

## Dónde empezar y qué esperar

- **Aportes bienvenidos:** reportes de errores, ideas, revisión del diseño, casos de prueba (por ejemplo, patrones de exposición bien documentados) y correcciones pequeñas de código.
- **Por dónde entrar:** busca las *issues* con la etiqueta [`good first issue`](https://github.com/Alexmedina-Dev/AgentReach/labels/good%20first%20issue) o [`help wanted`](https://github.com/Alexmedina-Dev/AgentReach/labels/help%20wanted). Si aún no hay ninguna que te sirva, abre una *issue* contando qué quieres hacer **antes** de empezar un cambio grande. Si tomas una issue existente, comenta en ella que la tomas antes de programar, para que nadie la repita.
- **Qué pasa después de abrir tu Pull Request:** (1) corre la revisión automática; (2) quien mantiene el repo lo revisa y puede pedirte cambios con comentarios; (3) cuando está bien, lo une con «Create a merge commit», que conserva tu autoría. Tú no unes tu propio Pull Request.
- **Tiempos:** quien mantiene el repositorio revisa los Pull Requests cuando puede; no hay un plazo garantizado.
- **Licencia de tu aporte:** al enviar un Pull Request, tu aporte se publica bajo la licencia Apache-2.0 del proyecto (sección 5 de la licencia).
- **Sistemas:** hoy el proyecto se prueba solo en Windows (la revisión automática corre en Windows). Si usas macOS o Linux, tu aporte es bienvenido: dilo en el Pull Request, porque las pruebas pueden comportarse distinto.
- **Tu correo:** tus commits llevan tu nombre y el correo que tengas configurado en git, y este repositorio es público. Si no quieres que se vea tu correo, usa el correo anónimo que GitHub te da (Settings → Emails).
- **Más contexto del proyecto:** `README.md`. Las notas de diseño (arquitectura e historias) viven en la rama `development`, en la carpeta `_bmad-output/`.

## Preparar el entorno

Necesitas [uv](https://docs.astral.sh/uv/) (gestor de paquetes y entornos de Python). No hace falta instalar Python aparte: uv descarga la versión 3.12 o superior que el proyecto pide.

### Si no mantienes el repositorio (lo normal)

No puedes subir ramas al repositorio original, así que trabajas en una copia propia (*fork*):

1. Necesitas una cuenta de GitHub (es gratis: https://github.com/signup). Luego, en la página del repositorio, pulsa **Fork**. Eso crea tu copia, en `https://github.com/<tu-usuario>/AgentReach`.
2. Clona **tu copia**, en la rama `development`, y crea una rama para tu cambio:

```powershell
git clone -b development https://github.com/<tu-usuario>/AgentReach.git
cd AgentReach
git checkout -b mi-cambio    # una rama por cambio; nunca trabajes directo en development
git branch                   # la rama activa lleva un *: debe ser mi-cambio, no development
uv sync                      # crea .venv e instala las dependencias de desarrollo
uv run agentreach --version  # comprueba que la CLI (interfaz de línea de comandos) funciona
```

3. Haz tu cambio, corre las pruebas (ver abajo) y súbelo a tu copia: `git push origin mi-cambio`.
4. En GitHub, abre un **Pull Request** (una petición para que tu cambio se una al proyecto) desde tu rama hacia la rama **`development`** del repositorio original (nunca hacia `main`).

### Si mantienes el repositorio

Clonas directamente el repositorio original, creas una rama desde `development` y abres el Pull Request hacia `development`:

```powershell
git clone -b development https://github.com/Alexmedina-Dev/AgentReach.git
cd AgentReach
git checkout -b mi-cambio
```

### En los dos casos

- **Trabaja en una sola carpeta:** las ramas cambian, la carpeta no. No clones el repo varias veces.
- **Nunca subas directo a `development` ni a `main`**: todo cambio entra por Pull Request. GitHub lo exige.

### Mantén tu copia al día

`development` cambia cada vez que se une un Pull Request. Si tu copia se queda atrás, tu Pull Request puede **chocar** con cambios nuevos o deshacerlos sin querer. Por eso, trae lo nuevo de `development` **antes de crear tu rama y otra vez antes de abrir el Pull Request**:

```powershell
# Una sola vez: registra el repositorio original con el nombre "upstream"
# (solo si trabajas desde tu fork; quien mantiene el repo ya lo tiene como "origin")
git remote add upstream https://github.com/Alexmedina-Dev/AgentReach.git

# Antes de crear tu rama: pon tu development al día
git checkout development
git fetch upstream
git merge --ff-only upstream/development   # quien mantiene el repo usa: git pull --ff-only origin development
git checkout -b mi-cambio

# Antes de abrir el Pull Request: pon tu rama encima de lo último de development
git fetch upstream
git rebase upstream/development            # quien mantiene el repo usa: git rebase origin/development
uv run pytest
git push --force-with-lease origin mi-cambio
```

Qué hace cada comando poco común:

- `--ff-only`: solo avanza tu `development` si no hay nada que mezclar; si no puede, se detiene en lugar de crear una mezcla confusa.
- `git rebase`: reordena tus commits para que queden encima de lo último de `development`, como si hubieras empezado hoy.
- `--force-with-lease`: sube tu rama aunque su historia cambió por el `rebase`, pero se niega si otra persona la tocó. Úsalo solo en **tu** rama, nunca en `development` ni en `main`.

Si `git rebase` marca un **conflicto**, git te dice qué archivos chocan. Arréglalos, usa `git add <archivo>` y `git rebase --continue`. Si te pierdes, `git rebase --abort` deja todo como estaba. Tu fork en GitHub también tiene un botón **Sync fork** que hace lo mismo para tu `development`.

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

**Resultado esperado en Windows**, sin modo desarrollador y sin `playwright`: pasan casi todas (unas 1900) y se omiten unas 40 (enlaces simbólicos, navegador y pruebas solo para POSIX, es decir, para macOS y Linux). Un fallo es real: corrígelo antes de abrir el Pull Request. Para reproducir exactamente la revisión automática de GitHub añade `$env:CI = "true"`: así las pruebas que se omitirían por falta del proyecto de prueba cuentan como fallo.

- **Un cambio de código lleva su prueba.** Si arreglas un error, añade una prueba que **falle sin tu arreglo** y pase con él.
- **No corras «ruff format .»:** hoy reescribiría unos 110 archivos que no cambiaste, y la revisión automática no lo exige.
- Las pruebas de `tests/reglas_no_negociables/` comprueban las reglas de abajo. Un cambio que haga fallar una de ellas no se acepta.

### El proyecto de prueba (secretos falsos)

Varias pruebas, entre ellas todas las de reglas no negociables y las que comparan contra respuestas conocidas, auditan un **proyecto de prueba**: una carpeta con secretos **falsos** que genera `pruebas/generar_proyecto_prueba.py`. Esa carpeta **no se sube al repositorio** y debe estar **fuera** de él (el generador se niega a crearla dentro, o en OneDrive).

Sin la variable `AGENTREACH_PROYECTO_PRUEBA`, **más de cien pruebas se omiten (*skipped*) en silencio**. En GitHub, la revisión automática (CI) las trata como fallos, así que corre las pruebas con el proyecto de prueba antes de abrir tu Pull Request.

## Reglas no negociables

Todo cambio debe respetarlas. Si un cambio las rompe, no se acepta.

1. **Solo lectura.** AgentReach nunca modifica el proyecto ni el entorno que analiza. No se abren archivos para «probar» permisos. Fuera de lo analizado solo escribe `--salida` y la carpeta `AgentReach-reportes` de la carpeta personal; durante la revisión no lanza programas, y al terminar solo abre el reporte HTML en el navegador si la persona lo permitió.
2. **Sin red durante la revisión.** Ninguna conexión de red salvo la consulta del número de versión: solo al abrir, cada 15 días como máximo, en `infra/actualizacion.py` (esa consulta ya está en `development` y llegará a `main` con la próxima versión). No se añaden dependencias que usen red.
3. **Sin valores de secretos.** Ningún reporte, registro ni mensaje de error contiene el valor de un secreto: solo ubicación, tipo y nivel de confianza.
4. **Solo biblioteca estándar** de Python como dependencia en tiempo de ejecución (lo que viene con Python, sin instalar nada más). Las herramientas de desarrollo (pytest, ruff) van en el grupo `dev`.
5. **Niveles de confianza:** cada hallazgo es *comprobado*, *potencial* o *hipótesis*. No se afirma que algo es alcanzable solo porque exista una referencia.
6. **Lo propio de cada sistema operativo** (permisos, rutas, *junctions*: accesos directos especiales de Windows) va aislado en `infra/`; el diseño no se ata a Windows.
7. **Decisiones abiertas:** si el documento de requisitos o el de arquitectura dejan algo abierto, no lo decidas en el código. Deja una nota `TODO` (pendiente) que cite la decisión y abre una *issue* para consultarlo.

### Estructura del código

Solo te hace falta si vas a tocar el código. `src/agentreach/` separa el núcleo (las reglas del análisis) de lo que lo rodea (leer archivos, hablar con cada plataforma, escribir reportes). Los paquetes son `contracts/` (modelo de hallazgo y puertos, o sea, las «tomas» que el núcleo ofrece), `core/`, `collectors/`, `infra/`, `adapters/`, `reporting/`, `config/`, `app/` y `cli/`. Cada paquete tiene un docstring (texto de explicación al inicio) que dice su responsabilidad.

## Ramas, commits y Pull Requests

| Rama | Para qué sirve |
|---|---|
| `main` | Lo publicable. Está protegida y no se empuja a ella directamente. |
| `development` | Aquí llegan los aportes de contribuyentes y se hacen todos los cambios. **Tu Pull Request apunta a esta rama.** También tiene las notas de planificación del proyecto (`_bmad-output/`). |
| `PruebaAlex` | Archivo de la etapa anterior del proyecto. Ya no se usa: no se contribuye ahí. |

- Crea tu rama desde `development` y abre el Pull Request hacia `development`, nunca hacia `main`.
- **Nombre de la rama:** corto y que diga qué haces; puedes usar el tipo del commit como prefijo (`fix/ignorar-venv`, `docs/mejorar-guia`). No hay un formato obligatorio.
- Rellena la plantilla `.github/pull_request_template.md` al abrir el PR (si usas BMAD, se llena sola con `bmad-create-pr`; si no lo usas, en «Story / Épica» escribe «no aplica»). Antes de abrirlo corre `uv run pytest` y `uv run ruff check .`: la revisión automática hace lo mismo y debe quedar en verde.
- Las ramas protegidas y su configuración las gestiona solo la persona dueña del repositorio.
- **Mensajes de commit:** `tipo: resumen en imperativo, en minúscula y sin punto final` (por ejemplo, `fix: ignorar la carpeta .venv`). Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `revert`. Más detalle en `.github/commit_template.md`.
- Un commit = un cambio con sentido, con sus pruebas y documentación. Un Pull Request por cambio.
- **Versiones:** al lanzar se sube el tercer número (`0.1.0` → `0.1.1` → `0.1.2`) en `pyproject.toml`. El aviso de versión compara esos tres números con los de `main`. Esto lo hace quien mantiene el repo.

## Proponer un adaptador nuevo

Un adaptador traduce las reglas y la configuración de una plataforma de agente (por ejemplo Claude Code u opencode) al modelo de hallazgo común. Cada adaptador **declara qué control real ofrece**: solo auditar, auditar y advertir, o auditar y bloquear.

1. Abre una *issue* (propuesta en GitHub) con: plataforma, versión, archivos de configuración y su precedencia, con enlaces a la documentación oficial.
2. Implementa el adaptador en su propio paquete usando solo lo que ofrece `contracts/` (nunca importes el núcleo directamente).
3. El adaptador **nunca recibe valores de secretos**: descarta los valores al leer la configuración.
4. Debe pasar las pruebas que todo adaptador cumple (`adapters/conformance/`) y las tres pruebas de reglas no negociables.
5. Documenta la capacidad declarada y cualquier límite conocido.

La forma de registrar adaptadores de terceros (puntos de entrada de Python o adaptadores dentro del repositorio) sigue en discusión en el borrador de arquitectura; consulta antes de empezar.

## Problemas comunes

- **Usa una ruta corta** para el proyecto de prueba (como `C:\dev\pp`): una ruta larga rompe la prueba del tope de 12 líneas (`test_historia_32`) aunque tu código esté bien.
- **`symlink: no creado - OSError: [WinError 1314]`** al generar el proyecto de prueba: es lo esperado si tu Windows no permite enlaces simbólicos (hace falta el modo desarrollador o ser administrador). No es un error. Esas pruebas se omiten en tu equipo, y GitHub sí las corre.
- **Pruebas con navegador** (reporte HTML): se omiten si falta `playwright`, y la revisión automática de GitHub tampoco las corre. Para correrlas tú: `uv run --with playwright pytest tests/test_historia_42.py` (usan Edge o Chromium).
- **Las pruebas esperan los mensajes en español.** Si tu sistema está en otro idioma, usa `$env:AGENTREACH_IDIOMA = "es"` y `$env:PYTHONUTF8 = "1"`, como hace `.github/workflows/ci.yml`.
- **Para ver por qué se omite una prueba:** `uv run pytest -rs`.
- **Editar archivos en Windows:** si los editas con PowerShell 5 (`Set-Content`, `>`), puede colarse un carácter invisible (BOM) al inicio del archivo. Usa un editor de texto como VS Code, que no lo añade.
- **Para quitar el proyecto de prueba:** `uv run python pruebas/generar_proyecto_prueba.py --limpiar "<carpeta>"`. Bórralo así y no a mano: el generador deja algunos archivos con permisos negados a propósito.
