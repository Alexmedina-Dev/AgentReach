---
title: 'Historia 11b - Correcciones H1 a H4 de la revision de las historias 9 a 11'
type: 'bugfix'
status: 'done'
---

## Resumen

Regla nueva: **si no se entiende un archivo de configuracion, el nivel nunca es "comprobado"**. `ResultadoAdaptador.reglas_incompletas`
(una fuente de reglas existe y no se leyo o no se entendio) hace que `postura_para` devuelva "no determinada" y `calcular` lo deje en
potencial con "no determinado".
- **H1:** JSON de Claude Code con comentario, cortado, UTF-8 invalido, elemento que no es texto, enorme, forma rara o demasiado
  anidado; lo mismo en opencode. Un permiso denegado al consultar un archivo ya no cuenta como "no existe".
- **H2 (opcion A de Alex):** la configuracion del usuario y la gestionada se leen SIEMPRE, solo por sus reglas (del bloque `env` de
  esas fuentes no se lee nada: ni valores, ni nombres, ni la limpieza del entorno); tambien `managed-settings.d/*.json`, `XDG_CONFIG_HOME`,
  `OPENCODE_CONFIG` y `opencode.jsonc` gestionada. El opt-in de ubicaciones sensibles solo gobierna lo que no son reglas.
- **H3:** `coincide` sigue la sintaxis gitignore que documenta Claude Code (verificado en la documentacion de permisos el 2026-11-10):
  nombre sin barra en cualquier profundidad, `dir/**` de una carpeta en cualquier profundidad (deny/ask), `/ruta` anclada a la carpeta de la
  fuente (`~/.claude` en la de usuario), `//c/**` y `//C:/**`, comparacion tambien por la ruta real; vacio, `!`, `[ ]`, `{ }` y barra invertida
  dan "no determinado" y se dicen en "no se pudo revisar". Un deny entendido manda aunque otro patron no se entienda.
- **H4:** `agent.*.permission`, `agent.*.tools`, `tools`, `mode` y la carpeta `.opencode/` dejan el nivel sin determinar; motivo nuevo
  `funcion_no_modelada` (tambien para hooks `PreToolUse`, `sandbox` y `allowManagedPermissionRulesOnly` de Claude Code).
- Pruebas de punta a punta con `auditar()` (`tests/test_correcciones_11b.py`, 56 casos) y una mutacion (desactivar la marca) hace fallar 9.
- `tests/conftest.py`: cada prueba ve un home y una carpeta de programas vacios (la configuracion real de quien corre las pruebas no cuenta).

## Review Triage Log

### 2026-11-10 - Review pass
- verdicts: 11 findings (un revisor independiente) - high 2, medium 5, low 4, false 0
- `[high]` `[patch]` los tipos de bytes de git dependian de las reglas de lectura (un archivo roto bajaba el codigo de salida): `TH-18` pasa a no depender de la postura (como lo que el agente carga solo; `CARGA_SOLA`), y esos hallazgos salen con "sin regla" y una vez; `tools`, `mode`, `agent.*.tools` y `.opencode/` de opencode
- `[medium]` `[patch]` el bloque env del usuario/gestionada se leia; claves de Claude Code que cambian lo que se lee; fragmentos gestionados, XDG, OPENCODE_CONFIG; comparacion por ruta real; permiso denegado = no existe
- `[low]` `[patch]` patron no interpretado dicho en "no se pudo revisar"; motivo propio para H4; `home` relativo; aislamiento de pruebas tambien en POSIX
- `[defer]` politica por registro/MDM de Windows para la configuracion gestionada; `opencode.json` de carpetas padre hasta la raiz de git; una carpeta `.claude` con junction o un `settings.json` enlazado dejan el nivel sin determinar (seguro, pero ruidoso); `Read(...)` con enlaces simbolicos de archivo (sin privilegio para probarlo)

## Auto Run Result

Verificacion: 1177 pasan / 13 omitidas / 1 xfail con el proyecto de prueba; 1037 / 153 / 1 sin el. Ruff limpio. Sin commit.
