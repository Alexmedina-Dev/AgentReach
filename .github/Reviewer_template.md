# Lista de revisión de Pull Requests (AgentReach)

> Para quien revisa un PR: una persona o la skill `bmad-review-pr-teammate`. Parte del esqueleto de la plantilla estándar de BMAD y la adapta a AgentReach, que es una herramienta de seguridad: **un PR que rompa una regla de seguridad no se une, aunque la revisión automática salga en verde.**
> Si una «puerta de entrada» falla, no sigas revisando lo demás.

## Antes de empezar

* [ ] Leí la issue enlazada (`Closes #N`), no solo el diff
* [ ] Sé qué tipo de cambio es (feat, fix, docs…) y que el PR va a **`development`**. Solo los PRs de documentación que abre el mantenedor van a `main`
* [ ] Es acotado: hace lo que dice la issue y nada más

## Puerta de entrada

* [ ] La revisión automática (`pruebas`) pasa
* [ ] **Si viene de un fork,** antes de pulsar «Approve and run workflows» leí «Files changed». No toca `.github/workflows/`, `pyproject.toml`, `uv.lock`, `pruebas/`, `_bmad/` ni `.claude/`, salvo que la issue lo pida
* [ ] Sin supresores de avisos (`# noqa`, `# type: ignore`) sin un comentario que explique por qué
* [ ] No mezcla el cambio con un refactor grande que no tiene que ver; si lo hace, se pide separarlos

## Reglas de seguridad (no se rompen nunca)

* [ ] **Solo lectura:** no escribe en el proyecto ni en el entorno que se analiza
* [ ] **Sin red:** no importa `socket`, `urllib`, `http`, `requests` ni similares. La única excepción es el aviso de versión (`infra/actualizacion.py` y quien lo llama)
* [ ] **No ejecuta programas:** sin `subprocess`, `os.system`, `eval` ni `exec`. La única excepción es `infra/actualizacion.py`
* [ ] **Sin valores de secretos** en reportes, registros, mensajes de error ni pruebas (los secretos de prueba se generan al correrlas)
* [ ] **Sin dependencias nuevas** en tiempo de ejecución: `pyproject.toml` no suma nada fuera del grupo `dev`
* [ ] No afirma «comprobado» sin fuente verificada: un nivel de confianza no sube por una suposición

## Diseño

* [ ] Respeta la arquitectura: lo propio de cada sistema operativo va en `infra/`
* [ ] No duplica lógica que ya existe; los nombres se entienden sin el contexto del PR
* [ ] Sin abstracciones «por si acaso», sin código muerto ni `print` de depuración
* [ ] Si toca la plantilla HTML del reporte, cambió **las dos copias idénticas**: `src/agentreach/reporting/plantilla_reporte.html` y `docs/reporte-html/plantilla.html`
* [ ] No decide en el código lo que el PRD o la arquitectura dejan abierto (para eso se abre una issue)

## Pruebas

* [ ] Hay pruebas nuevas que cubren el cambio, no solo «las viejas siguen pasando»
* [ ] **Las pruebas nuevas fallan sin el cambio.** Compruébalo: deja las pruebas, vuelve el código a como estaba y córrelas; deben fallar
* [ ] Cubren casos límite razonables (mayúsculas y minúsculas en Windows, rutas con espacios, vacío, varios niveles)
* [ ] `uv run pytest` y `uv run ruff check .` pasan. No se corrió `ruff format .` sobre todo el repo

## Privacidad y datos

* [ ] Sin correos, nombres reales ni rutas locales **dentro de los archivos**. El correo del autor del commit es suyo: no se le pide cambiarlo
* [ ] Sin datos de empresas, clientes ni proyectos reales
* [ ] Sin archivos binarios o muy grandes sin un motivo claro

## Documentación

* [ ] Si cambia algo visible, se actualizaron el README, `CONTRIBUTING.md`, la ayuda del programa o los documentos que lo mencionan
* [ ] El PR llenó la plantilla `.github/pull_request_template.md` y el commit sigue `tipo: resumen en minúscula y sin punto final`

## Cómo comentar

| Etiqueta | Significa | ¿Bloquea? |
| --- | --- | --- |
| `praise:` | Algo quedó bien hecho; reconócelo | No |
| `nit:` | Detalle menor; el autor puede ignorarlo | No |
| `suggestion:` | Propones una mejora; el autor decide | Depende: dilo claro |
| `issue:` | Hay que corregirlo antes de aprobar | Sí |
| `question:` | Pides una aclaración | No |

Si de verdad bloquea, usa `issue:`. No lo suavices como `nit:`: eso enseña a ignorar los comentarios importantes. A quien contribuye por primera vez, empieza por agradecer y reconoce lo bueno.

## Veredicto

* [ ] **Decision-needed:** algo que solo el autor o quien mantiene el repo puede decidir
* [ ] **Patch:** corrección menor que el autor aplica sin discusión
* [ ] **Deferred:** hallazgo válido que no bloquea este PR; se registra para después
* [ ] **Dismissed (noise):** se consideró y no aplica; se explica por qué

**Resultado final:** Approve / Request changes / Comment

## Para quien mantiene el repositorio

* [ ] Se une con **«Create a merge commit»**, y solo si la revisión automática pasó
* [ ] **Cierra la issue a mano.** Aunque el PR diga `Closes #N`, GitHub solo cierra la issue sola cuando el PR se une a la rama principal (`main`), y estos PRs van a `development`. Ciérrala con un comentario (por ejemplo, el de agradecimiento)
* [ ] Una contribución nunca cambia las reglas del proyecto ni los ajustes de GitHub

---

## Reglas específicas del proyecto

* [ ] Revisé el PR contra [`AGENTS.md`](../AGENTS.md) y [`CONTRIBUTING.md`](../CONTRIBUTING.md), que son la fuente de verdad de las reglas
