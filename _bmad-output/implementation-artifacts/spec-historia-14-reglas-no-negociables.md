---
title: 'Historia 14 - Pruebas de las reglas no negociables'
type: 'feature'
status: 'done'
---

## Resumen

Las tres pruebas omitidas (`skip`) pasan a ser reales y se anaden dos: `tests/reglas_no_negociables/` con `test_solo_lectura.py`,
`test_sin_red.py`, `test_sin_valores_de_secretos.py`, `test_sin_ejecutar_programas.py` y `test_limites_duros.py`, mas un
`conftest.py` con la vigilancia. La vigilancia es un **gancho de auditoria** de Python (`sys.addaudithook`): ve cualquier via
(`open`, `io.FileIO`, `_io`, `os.*`, `socket.*`, `subprocess`) y lanza `ViolacionDeRegla`, que hereda de `BaseException` para que
ningun `except Exception` del producto la trague; ademas anota cada intento y la prueba falla al terminar si hay alguno. Cada
vigilancia tiene su prueba de que funciona. Auditan el proyecto de prueba completo (trampas incluidas) con la carpeta personal
falsa y el opt-in. Pruebas estaticas: el producto no importa modulos de red ni `subprocess`, no llama a nada que lance procesos,
no escribe fuera de `--salida`, y `ctypes` solo vive en cinco modulos de medicion (lista blanca, sin nombres de proceso).
Sin el proyecto de prueba se saltan, salvo en CI (`CI` o `AGENTREACH_EXIGIR_PRUEBAS`), donde fallan.

## Review Triage Log

### 2026-11-10 - Review pass
- verdicts: 12 findings (un revisor independiente, con experimentos que demostraron 5 violaciones sin detectar) - high 4, medium 5, low 3
- `[high]` `[patch]` la vigilancia por parches de nombres no veia `io.FileIO`, `_io.open`, `nt.system`, `ctypes` ni `_socket`; las trampas eran `Exception` y los `except Exception` del producto podian tragarlas; los `skip` silenciosos - todo se rehizo con el gancho de auditoria, trampas `BaseException`, registro de intentos y falla en CI
- `[medium]` `[patch]` el inventario de secretos solo miraba `.env` (ahora tambien `credentials.json`, `.aws/credentials`, `.git/config` y `.npmrc`; valores, minusculas y base64; texto sin saltos para que el ajuste de linea no esconda un valor; prueba con `--ancho 20`); el espia de `open` no veia `Path.read_text`, `io.open` ni `io.FileIO` y corria solo en la carpeta hostil (ahora es un gancho, corre tambien sobre el proyecto de prueba completo y normaliza rutas); la instantanea ignoraba atributos y ctime; tope de tiempo real con un hilo; limites 64/65 niveles
- `[low]` `[patch]` AST ampliado (`write_text`, `mode=`, `__import__`); error forzado y `--salida` tambien en ingles
- `[defer]` la carpeta hostil se audita aparte y no dentro de una copia del proyecto de prueba (copiar la junction cambia el arbol); JSON anidado solo en `.claude/settings.json` (otros archivos de configuracion: `.mcp.json`, `.vscode/tasks.json`, opencode); la ACL (SDDL) no entra en la instantanea; `ctypes.call_function` no se vigila (la sonda lo necesita): lo cubre la lista blanca estatica
- `[reject]` `pytest-timeout` (se usa un hilo con `join`)

## Auto Run Result

Verificacion: 1051 pasan / 12 omitidas con el proyecto de prueba; 986 / 77 sin el. Ruff limpio. Sin commit.
