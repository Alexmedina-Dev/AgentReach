# Revisión independiente, historias 1 a 3

Fecha: 2026-11-09. Revisor: agente independiente, solo lectura (no se tocó src, tests ni documentos; solo se escribió este informe y un script temporal en la carpeta de trabajo temporal, fuera del proyecto).

## Resultados ejecutados (verificado ejecutando)

- `uv run pytest -q`: 86 pasan, 7 omitidas, 0 fallan.
- `uv run ruff check src tests`: "All checks passed!".
- Las 7 omitidas: 3 son módulos completos de reglas no negociables que son solo un `pytest.skip` ("sin red", "sin valores de secretos", "solo lectura"); 1 es solo POSIX; 3 dependen de la variable `AGENTREACH_PROYECTO_PRUEBA` (no estaba definida).
- Repetí `tests/test_recorrido.py` y `tests/test_permisos_windows.py` con la variable apuntando a `C:\dev\proyecto-prueba-agentreach`: 23 pasan, 2 omitidas (EN-03, el enlace simbólico no existe; y la de POSIX). Es decir, EN-01, EN-02, NO-02, NO-05, PP-03, PP-04, PP-05 y PA-01 pasan contra el proyecto real, pero un `pytest` normal NO los ejecuta.
- No se ejecutó nada de `trampas*`.

Los escenarios de ataque siguientes los probé con un script propio sobre carpetas temporales (junction real creada con `_winapi.CreateJunction`).

## Veredicto

Base sólida y disciplinada (sin red, sin subprocess, sin escritura, sin valores de secretos en mensajes; el localizador nunca copia valores). Pero hay un hueco real de seguridad de rutas en `leer_texto` y un caso en que la sonda de Windows devuelve "legible y abierto a todos, sin ambigüedad" para algo que no es un archivo. Recomiendo corregir A1 y A2 antes de la Historia 4. Nada crítico.

## Hallazgos

### Altos

**A1. `leer_texto` sigue enlaces que están en una carpeta intermedia** (`src/agentreach/infra/fs_solo_lectura.py` línea ~75-90). Verificado ejecutando.
- `_es_enlace(ruta)` y `lstat` solo miran el último componente. Si `proyecto/enl` es una junction hacia una carpeta externa, `leer_texto("proyecto/enl/secreto.env")` devolvió el contenido del archivo externo (`K=CANARIO`). Contradice el docstring del módulo ("no sigue enlaces") y FR-19 / decisión del 2026-11-09 (solo se reporta el enlace).
- Hoy `recorrer` no entra a enlaces, así que no se explota todavía. Pero los detectores futuros (Historias 4 a 10) pedirán rutas fijas como `.claude/settings.json`; si `.claude` es una junction a otra carpeta, se lee fuera del proyecto, y puede entrar contenido ajeno al reporte.
- Arreglo: antes de abrir, comparar `os.path.realpath(ruta)` con `realpath(raiz del proyecto)` (la raíz debe pasarse al puerto o al constructor) y rechazar si sale; o recorrer componente a componente con `lstat`. En POSIX además abrir con `os.open(..., O_RDONLY | O_NOFOLLOW | O_NONBLOCK)`. Añadir prueba: junction en carpeta intermedia.

**A2. La sonda de Windows da un nivel engañosamente alto con nombres de dispositivo** (`sonda_windows.py`, `_evaluar`, ~línea 175-215). Verificado ejecutando.
- `evaluar("NUL")` (ruta relativa, nombre reservado) devolvió `permiso=SI, abierto_a_todos=True, ambiguo=False`. El dispositivo tiene una ACL sin restricciones y la sonda lo trata como un archivo "comprobado, abierto a todos". Esto viola la regla "ante fallo, potencial o no determinado, nunca comprobado". `CON` con ruta completa sí cayó a NO_DETERMINADO, pero por casualidad (la API lo rechazó).
- Escenario: un detector pasa una ruta relativa o un nombre reservado y sale PA-01 "comprobado" falso.
- Arreglo: exigir ruta absoluta; antes de la API, `os.lstat` y comprobar que es archivo regular o carpeta (no dispositivo); rechazar nombres reservados (CON, PRN, AUX, NUL, COM1-9, LPT1-9, con o sin extensión), prefijos `\\.\` y rutas relativas, devolviendo NO_DETERMINADO y ambiguo. Añadir prueba con `NUL`, `CON`, `\\.\C:` y ruta relativa.

### Medios

**M1. Unicode engañoso no se limpia** (`contracts/finding.py` línea 71, `_CONTROL_RE`). Verificado ejecutando: `limpiar_ruta("a\u202eexe.txt\u200bb\u2066")` devuelve el texto intacto. Solo se quitan `\x00-\x1f` y `\x7f-\x9f`. Los controles de dirección (U+202A-202E, U+2066-2069), espacio de ancho cero (U+200B-200F, U+2060, U+FEFF) y separadores U+2028/2029 pasan, y un archivo `reporte\u202etxt.exe` se vería como `reportexe.txt` en el informe. Arreglo: quitar o escapar (`\u202e`) esas categorías (`unicodedata.category` en Cf, Zl, Zp). Mostrar escapado es mejor que borrar, para que la persona vea que había algo raro.

**M2. Se confunde la ruta mostrada con la ruta usada** (`fs_solo_lectura.py` `_metadatos`, línea ~44; `enlaces.py`, líneas ~97-110). La ruta guardada en `Metadatos.ruta` ya viene limpia (sin caracteres de control) y luego `recorrer` la reusa para `listar`. En POSIX una carpeta llamada `a\x07b` se vuelve `ab`: da error (se marca "no revisada") o, peor, lista otra carpeta distinta `ab`. Además `_destino` limpia el destino del enlace antes de `_sale_del_proyecto`: un enlace hacia `../proy\x7f` se evalúa como `../proy` ("dentro") y no se reporta aunque sale. Arreglo: conservar `ruta_real` sin limpiar para uso interno y `ruta` limpia solo para mostrar; evaluar destinos con el texto original. (En Windows no se pueden crear nombres con controles, por eso no se vio en la máquina de pruebas.)

**M3. TOCTOU y archivos especiales en `leer_texto`** (misma función). Se comprueba con `lstat` y luego se abre sin banderas. Si entre ambos se reemplaza el archivo por un enlace, la apertura lo sigue; en POSIX una tubería con nombre (FIFO) puesta en medio bloquea la apertura (denegación de servicio). Además, si el archivo crece, se devuelven hasta LIMITE_BYTES+1 bytes sin comprobar el largo leído. Arreglo: `os.open` con `O_NOFOLLOW|O_NONBLOCK`, `fstat` sobre el descriptor ya abierto y rechazar si `len(datos) > LIMITE_BYTES`. Verificado solo leyendo.

**M4. `realpath` y la regla "sin red"** (`enlaces.py` `_norm`, línea ~58). Solo se descartan destinos que empiezan por `\\` o `//`. Una junction hacia una unidad de red mapeada (`Z:\...`) hace que `os.path.realpath` consulte la red. Tampoco se comprueba si la raíz del proyecto está en una unidad de red mapeada. Arreglo: tratar `GetDriveTypeW == DRIVE_REMOTE` como ruta de red (sin consultarla), y no llamar `realpath` sobre destinos no locales. Verificado solo leyendo.

**M5. Las tres reglas no negociables del PRD no tienen prueba automática** (`tests/reglas_no_negociables/*`: solo `pytest.skip`). Mientras tanto la única vigilancia es `test_el_codigo_de_las_sondas_no_importa_modulos_de_procesos` (solo mira las dos sondas) y `test_el_sistema_de_archivos_..._no_tiene_escritura` (solo mira nombres de método, que no demuestra nada). Falta una prueba que escanee con `ast` todo `src/` en busca de `socket`, `urllib`, `http`, `ssl`, `subprocess`, `os.system`, `open(..., "w"/"a"/"x"/"+")`, `os.utime`, `os.chmod`, `shutil`, `Path.write_*`, y una prueba de hash y fecha de modificación del árbol antes y después de `recorrer` y `leer_texto`. Hoy esa disciplina descansa en revisión humana. Verificado ejecutando (las omisiones) y leyendo (código sin escrituras ni red: no encontré ninguna).

**M6. La sonda no abre el archivo, pero la prueba solo lo vigila en Python** (`test_permisos_windows.py`, `test_no_se_abre_el_archivo_medido`). `GetNamedSecurityInfoW` abre internamente el archivo (con permiso solo de leer la seguridad, no los datos), lo cual es compatible con el objetivo, pero la prueba solo parchea `open` de Python y no demuestra nada sobre la API. La documentación dice "nunca se abre el archivo"; conviene precisarla: "no se abre para leer datos". Además la sonda sigue junctions y enlaces simbólicos (verificado: archivo vía junction da SI): mide la ACL del destino sin avisar. Arreglo: marcar `ambiguo` si la ruta o un padre es enlace.

### Bajas

- **B1.** `_entradas` (`sonda_windows.py` ~línea 140): `ace.value` puede ser `None` y `from_address(None)` lanza `TypeError`, que no está en el `except` de `evaluar` (solo OSError, ValueError, UnicodeError, ArgumentError). Una falla rara tumbaría la tubería en vez de devolver no determinado. Arreglo: capturar `Exception` acotado o validar el puntero. Solo leyendo.
- **B2.** "Abierto a todos" solo reconoce el SID `S-1-1-0` (Todos). `BUILTIN\Users` (S-1-5-32-545) y Authenticated Users (S-1-5-11) quedan como no abierto. Decisión de producto: documentarlo en el PRD como límite conocido. Solo leyendo.
- **B3.** `listar` (`fs_solo_lectura.py`): un solo `stat` fallido (archivo borrado durante el recorrido) aborta toda la carpeta y se marca "no revisada". Es conservador, pero pierde todos los hermanos. Arreglo: manejar el error por entrada.
- **B4.** Sin tope de cantidad de entradas ni de tiempo en `recorrer` (carpetas enormes tipo `node_modules`): lentitud, no fallo. Los flujos de datos alternativos NTFS (`archivo:secreto`) no se enumeran; un secreto escondido ahí no se ve (verificado: `archivo:zz` en la sonda da NO_DETERMINADO). Documentar como límite.
- **B5.** `Pipeline.ejecutar`: si un detector falla, todo el informe falla (RuntimeError). Coherente con "nunca en silencio", pero deja la persona sin nada; considerar registrar "no revisado" y seguir. La cadena `from error` puede arrastrar rutas en la traza (no secretos). Solo leyendo.
- **B6.** `_comando` (Windows) arma `icacls "ruta"` con la ruta tal cual: un nombre con `%VAR%` se expandiría al pegarlo en cmd. Solo es texto para la persona, pero conviene advertirlo. En POSIX el escape con comillas simples es correcto y está probado.
- **B7.** `test_ruta_invalida_no_lanza_excepcion` usa `C:\carpeta\0rara` (no contiene un nulo real); no prueba la rama de `ValueError`. Yo probé `"C:\\a\x00b"` y sí cae a NO_DETERMINADO (verificado ejecutando); conviene que la prueba use ese caso.

## Lo que sí está bien (verificado)

- Sin `socket`, `subprocess`, `os.system` ni `open` en modo escritura en los archivos revisados (verificado leyendo; ctypes solo llama funciones de seguridad y libera con `LocalFree` y `CloseHandle` en `finally`).
- `AccessCheck`: tipos de argumentos declarados; los errores de la API caen a NO_DETERMINADO y ambiguo, o a NO con ambiguo (negativa 5). Ningún fallo conocido produce SI-inequívoco salvo A2.
- Enlaces: no se entra, las junctions con destino dentro del proyecto no se reportan, los bucles no se recorren, un enlace a ancestro o hermano con prefijo similar se reporta (`commonpath`). Prueba de ciclo existe.
- Ruta con nombre largo (300 caracteres), `\\?\`, `\\.\C:`, `::$DATA`, vacía y nulo: NO_DETERMINADO o equivalente sin excepción (verificado ejecutando). `.` final y 8.3 se normalizan al mismo archivo.
- Localizador: no devuelve valores, devuelve `None` ante duda; los errores no incluyen contenido.

## Contra el proyecto de prueba y el PRD

- Cubiertos y verificados con el proyecto real: EN-01, EN-02, NO-02, NO-05, AT-11 (solo que el enlace aparezca), PP-03, PP-04, PP-05, PA-01.
- No cubiertos: EN-03 (omitido, el enlace simbólico no se pudo crear; el camino de symlink no se probó con uno real en Windows), TR-01 (no corresponde a estas historias). El nivel de EN-01 hoy es `hipotesis`/`no_determinado` mientras el oráculo espera `potencial`; está declarado como provisional hasta la Historia 11, no es contradicción pero hay que cerrarlo ahí.
- `pytest` normal omite silenciosamente los casos del proyecto de prueba: conviene que `pyproject.toml` apunte a esa ruta por defecto o que la omisión falle en integración continua, para que no pasen "en verde" sin haberse ejecutado.

## Qué falta

1. Corregir A1 y A2 con sus pruebas. 2. Pruebas de reglas no negociables (M5). 3. Limpieza de Unicode engañoso y separar ruta mostrada de ruta usada (M1, M2). 4. Endurecer la apertura (M3) y rutas de red mapeadas (M4). 5. Un caso real de enlace simbólico (EN-03) en una máquina con permiso.

## Correcciones

Fecha: 2026-11-09. Pruebas nuevas en `tests/test_correcciones_review.py`.

- A1: `FsSoloLectura(raiz)` resuelve la ruta completa y, si sale de la raíz, lanza `FueraDelProyecto` (subclase de `ArchivoNoLegible`, sin contenido en el mensaje). Sin raíz rechaza cualquier ruta con un enlace en el camino. Apertura con `O_NOFOLLOW`/`O_NONBLOCK` donde existen. Falta: que los detectores pasen la raíz al construir `FsSoloLectura` (hoy usan el modo estricto sin raíz).
- A2: la sonda de Windows exige ruta absoluta local y archivo regular (carpeta solo con `permitir_carpeta=True`), rechaza nombres de dispositivo (CON, PRN, AUX, NUL, COM1-9, LPT1-9, con o sin extensión), prefijos `\.\` y `\?\`; cualquier fallo da no determinado y ambiguo.
- M1: `limpiar_ruta` quita categorías Cf, Zl y Zp (incluye U+202A-202E, U+2066-2069, U+200B-200D, U+2060, U+FEFF). Se quitan, no se escapan.
- M2: `Metadatos` gana `ruta_real` y `destino_real` (uso interno) y `ruta`/`destino_enlace` quedan solo para mostrar; el recorrido y el detector usan los reales.
- M3: se comprueba archivo regular antes y después de abrir (`fstat`) y se rechaza si se leyó más que el límite.
- M4: `es_ruta_de_red` (UNC o `GetDriveTypeW` remoto) evita `realpath` sobre destinos y raíces de red.
- M6 (parcial): la sonda marca `pasa_por_enlace=True` y ambiguo si la ruta pasa por junction o enlace.
- Sin cambios: M5 (reglas no negociables, historia 14), B1-B7.
