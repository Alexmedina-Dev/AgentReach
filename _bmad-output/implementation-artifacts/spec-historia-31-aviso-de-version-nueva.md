# Historia 31: aviso de versión nueva

**Estado: terminada (2026-11-17), rehecha sobre `development` (rama `historia-31-aviso-de-version`).**

## Qué hace
- Al abrir (después de la pantalla «qué hace y qué no hace», antes de las preguntas), como máximo cada 15 días, consulta el número de la última versión: `https://github.com/Alexmedina-Dev/AgentReach/raw/main/pyproject.toml`. Solo HTTPS, tiempo límite de 4 s, lectura de hasta 64 KB, `User-Agent: AgentReach/<versión>` y nada más (ni datos, ni cookies, ni claves).
- El número se valida con `[0-9]{1,4}.[0-9]{1,4}.[0-9]{1,4}(.dev[0-9]{1,4})?` (solo dígitos ASCII). Se compara el núcleo X.Y.Z.
- Con versión nueva: «Hay una versión nueva (X).», el comando exacto en su propia línea y «¿Descargarla ahora? (S/N)» (en inglés, Y/N). Solo s, S, n y N cuentan (y, Y, n, N en inglés); Enter no decide; tres intentos sin respuesta válida = no.
- Con S: al terminar el programa (nunca durante la revisión), si está instalado con uv (`…/uv/tools/agentreach` y `uv` en el PATH), ejecuta `uv tool install --reinstall git+https://github.com/Alexmedina-Dev/AgentReach` sin shell, con tiempo límite de 300 s y sin entrada; si no puede, muestra el comando. No se usa `uv tool upgrade`. **En Windows nunca se lanza** (decidido por Alex el 2026-11-17 tras la prueba real): con AgentReach abierto, `uv tool install --reinstall` falla con «Acceso denegado» al borrar `…\tools\agentreach\Scripts` y deja la instalación rota (`No module named 'agentreach'`; repararla exige ejecutar el comando con AgentReach cerrado). Quien lanza `uv` es el propio AgentReach, que sigue abierto, así que con S solo se muestra «En Windows AgentReach no se puede reemplazar mientras está abierto… Cierra esta ventana y ejecuta: <comando>». `puede_instalar_sola()` decide por el sistema. En macOS y Linux no se ha probado la reinstalación con el programa abierto (un sistema Unix sí deja reemplazar archivos en uso).
- Con N: sigue con la versión actual y vuelve a avisar a los 15 días.
- Silencios: sin internet, con error, con una versión que no entiende o sin terminal, ni avisa ni falla. No se consulta con `--formato`, `--salida`, `--json`, `--sin-actualizar` ni con `AGENTREACH_SIN_ACTUALIZAR`; tampoco `--help`, `--version` ni `doctor`.
- La fecha va en `ultima_comprobacion_de_version` de `preferencias.json` (`AgentReach-reportes`), sin pisar la otra preferencia. Archivo corrupto, fecha ilegible o en el futuro: no falla (toca consultar). Si no se puede anotar la fecha, no se consulta.
- Transparencia: la pantalla inicial dice que la consulta deja la IP, la hora y el nombre del programa, que cada 15 días revela que esa IP usa AgentReach, y cómo apagarla («no usa la red» pasó a «no usa la red durante la revisión»).
- Documentos: README (tres frases de «sin red» y sección «Version notice»), PRD (excepción en FR-2), CONTRIBUTING (regla 2 y regla de versiones: al lanzar se sube el tercer número).

## Decisiones para confirmar
1. **Redirección de GitHub:** `github.com/…/raw/…` responde 302 a `raw.githubusercontent.com`. Se permite **una**, solo HTTPS y solo a `github.com` o `raw.githubusercontent.com`, sin usuario ni puerto raro; otro destino se rechaza.
2. **Excepción a «no se lanzan programas»:** `subprocess` solo en `infra/actualizacion.py`, solo `run`, `shell=False`, con `timeout` (prueba estática). `urllib.request` solo ahí y en quien lo llama (`cli`).
3. **La fecha se anota antes de consultar** (una consulta fallida también cuenta: como máximo cada 15 días).
4. El aviso va antes de las preguntas de permiso.

## Pruebas
`tests/test_historia_31.py` (123): versión estricta, petición sin datos, cuerpos raros, límites, errores, redirecciones, comando exacto, instalación sin shell, flujo S/N/Enter en ES y EN, 15 días, preferencias corruptas, interruptores, nunca durante la revisión, revisión sin red con sockets bloqueados, transparencia y pruebas estáticas.

## No verificado
Instalación real con `uv` (la prueba usa un falso); reinstalar en Windows con `agentreach.exe` abierto puede fallar (entonces solo se muestra el comando); una terminal real.
