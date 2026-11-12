# Código real: reporte, catálogos, agentes, adaptadores y CLI (contraste con arquitectura-borrador.md)

Rutas relativas a `C:\dev\AgentReach\src\agentreach\` salvo indicación. Leído el 2026-11-11.

## (a) Capa reporting/

- **Compuerta** `reporting/gate.py`: `preparar` (l.173) autocomprueba (`autocomprobar`, l.185) y devuelve `DatosReporte` (l.114) con vistas congeladas de lista blanca (`HallazgoVista` l.42: ruta, línea, tipo, proveedor, nivel, motivo...). Docstring l.1-7: una vista "no tiene dónde guardar un valor de secreto ni el texto de un archivo"; `texto.py` y `html.py` nunca ven un `Finding`. Rutas pasan por `ruta_visible` (l.145) y `limpieza.escribir_peligrosos` (`limpieza.py`:34). `--agente` filtra aquí (l.190-199). `codigo_de_salida` (l.166): 0 / 1 (comprobados o `--estricto` con no revisados).
- **Terminal** `reporting/texto.py`: `generar` (l.656) → `_pasada` (l.634) arma secciones en orden: encabezado, resumen, configurados, no determinado, [modo `corto`: urgentes + alcance + cierre] o reglas, hallazgos, no revisado, términos (solo `--detalle`), cierre (l.634-653). Resumen (l.301): por agente, conteo por nivel con símbolos ■ ▲ ◊ (l.51; ASCII `[!!] [!] [?]` l.54) y "○ no se pudo revisar". Tono formal vía `_T_FORMAL` (l.188). Segunda barrera: si se escribió algo peligroso repite con nota (l.676-677).
- **Ancho y color** `reporting/formato.py`: ancho de trabajo = columnas acotadas a 60-100 (l.37, 52); `ajustar` (l.60) parte en límites de palabra, nunca parte palabras; `ancho_visible` (l.42) cuenta ancho doble/combinantes. Solo emite secuencias de color `m` (l.7, 299). `decidir_color` (l.226): `--color` > `NO_COLOR` > no-terminal/`TERM=dumb` > VT de Windows; 16 colores o 24 bits.
- **Tema de tres estados**: `resolver_tema_marca` (l.211) devuelve True claro / False oscuro / None desconocido; prioridad `--tema` > `AGENTREACH_TEMA` > `COLORFGBG` > desconocido. `resolver_tema` (l.186) es la versión de dos estados (desconocido = oscuro) para el texto. `reporting/marca.py`: banner en tres tamaños (`Tamano`, l.23; grande 61, mediano 69, mínimo 57 columnas), AGENT sin color propio y REACH `#07856C` si tema desconocido (docstring l.3-6, `REACH_UNIVERSAL` formato.py:118); no hay banner con <40 columnas, redirección, `NO_COLOR`, `--no-banner`, `--salida` (marca.py:56-65).
- **HTML** `reporting/html.py`: `generar_html` (l.229) sustituye el marcador `__AGENTREACH_DATA__` (l.43, una sola vez, l.236) de `plantilla_reporte.html` (l.618, `<script type="application/json" id="data">`) por JSON compacto; `_a_json_seguro` (l.219) escribe `<`, U+2028/9 escapados. Tope 20 MB y 20 000 hallazgos/agente (l.44-45). `construir_datos` (l.198) arma `schema_version` (=1, l.46), `agents`, `configured_agents`, `undetermined_traces`, `catalog` (solo entradas usadas, l.147), `not_reviewed`, `limits`, `glossary` (l.171: las 12 fichas con `labels` y `terms[{id,name,line,what_is,means,to_do}]`, cada texto `{en,es}` con el tono elegido). Sin recursos externos: CSP `default-src 'none'` (plantilla l.5). Las plantillas de `src/.../plantilla_reporte.html` y `docs/reporte-html/plantilla.html`: `diff -q` no reportó diferencia (identidad no confirmada de otra forma).
- **Esquema** `docs/reporte-html/esquema-datos.md` (versión 1; l.1) y `esquema-datos.schema.json` (`schema_version`, `glossary` l.419). Campos opcionales `initial_language`, `configured_agents`, `agents[].not_determined`, `glossary`. Reglas de seguridad l.89-96: nunca valores de secretos, rutas limpias, topes, sin HTML crudo, cero red.
- **Qué NO puede pasar**: valores de secretos o contenido de archivos llegan al texto/HTML; lo respaldan la estructura de las vistas y pruebas (`tests/reglas_no_negociables/test_sin_valores_de_secretos.py`, `tests/oraculo/test_oraculo.py` usan marcadores canario; no verifiqué su alcance exacto sobre HTML).

## (b) Catálogos

- `contracts/finding.py`: `Tipo` = 20 (TH-1..TH-20, l.122-144); `CATALOGO_EXPLICACIONES` (l.281) con 20 entradas `{ES, EN}: (qué significa, qué hacer)`; `Motivo` = 9 valores (l.147), que explican el nivel. `texto_de_motivo` en l.522.
- `core/catalogo_explicaciones.py`: títulos por tipo (`TITULO_TIPO` l.45, 20), `MotivoNoRevisado` = 12 (`contracts/no_revisado.py`:15; `TITULO_MOTIVO` l.83 y `COMO_RESOLVER` l.107, 12), proveedor, postura, ajeno, `LIMITES` (6 por idioma, l.181) y `LIMITES_TAMBIEN`. `Tono` (l.215): CERCANO/FORMAL; `EXPLICACIONES_FORMAL` (l.223, 20) y `COMO_RESOLVER_FORMAL` (l.250) sobrescriben el español de "usted". Funciones `que_significa`, `que_hacer`, `como_resolver` (l.268-288).
- `core/catalogo_terminos.py`: `Termino` (l.22) = 12 fichas (3 niveles, no determinado, no se pudo revisar, hook, sandbox, configurado vs analizado, autocomprobación, lugar no confirmado, código de salida, camino de alcance). `Variantes(tu, usted, en)` (l.38); `Ficha` con `linea` (≤90 caracteres) y `que_es/que_significa/que_hacer`. Verificado ejecutando: `len(FICHAS)=12`.
- Todo texto sale de tablas fijas; ningún modelo de lenguaje (docstrings de `catalogo_explicaciones.py`:1-6 y `html.py`:1-8).

## (c) Reconocimiento de agentes

- `data/catalogo-agentes.json` (2699 líneas): lista de 22 entradas: 18 agentes (claude-code, opencode, gemini-cli, codex-cli, copilot-vscode, copilot-cli, cursor, windsurf, kiro, cline, roo-code, continue, aider, amp, junie, qwen-code, antigravity, goose), 2 marcos (gentle-ai, bmad) y 2 "agente personalizado" omitidos (`OMITIDOS`, agentes.py:~68). Campos: `proyecto`, `usuario`, `entorno`, `firma_fuerte`, `firma_debil`, `falsos_positivos`, `verificado`...; no hay un campo `firmas`, por lo que "cuántas firmas" no lo conté.
- RECONOCER vs ANALIZAR: `ANALIZADOS = {claude-code, opencode}` (agentes.py:~65): solo esos tienen adaptador; el resto solo se muestra "configurado" (`AgenteDetectado.analizado`, l.~52). Dice "configurado", nunca "ejecutado" (docstring l.3-6). Solo mira existencia de archivos y NOMBRES de variables de entorno.
- Confianza (l.~21-25 y docstring): alta = firma fuerte verificada; potencial = fuerte sin fuente verificada; hipótesis = solo indicios débiles con un único candidato.
- Nombres compartidos: `COMPARTIDOS` (l.~71: `agents.md`, `.mcp.json`, `.vscode`, `.github`, `.env`, `.gemini`, `.agents`...) nunca identifican un agente; salen como `NoDeterminado` con candidatos (`_no_determinados`, l.309).
- GitHub Copilot: `_unificar_copilot` (l.249): si la única señal es `.github/copilot-instructions.md` o `.github/instructions/*.instructions.md` (compartida por VS Code y CLI), se reconoce UN agente "GitHub Copilot (VS Code o su línea de comandos)" (l.237-238), no dos.
- Copia docs: `docs/agentes-catalogo/catalogo-agentes.json` es byte a byte idéntica (verificado con `cmp`). La vigila `tests/test_historia_24.py:51` (compara `read_bytes` de ambas).

## (d) Adaptadores

- `adapters/base.py`: `ResultadoAdaptador` (l.57: reglas, nombres de entorno, agentes definidos, `config_proyecto`, `no_revisados`, `esquema`...) y protocolo `AdaptadorBase` (l.71: `plataforma`, `capacidad`, `cargar`, `postura_para`, `regla_para`). Un adaptador nunca lanza por configuración rara: informa `NoRevisado`.
- `adapters/claude_code/__init__.py`: lee config en cuatro niveles gestionada/local/proyecto/usuario; reglas allow/ask/deny; de `env` solo nombres; fuentes de usuario y gestionada siempre solo por reglas (docstring l.1-9). `reglas.py` (precedencia deny > ask > allow, l.20). Hallazgos propios: TH-10 y TH-11. `DetectorClaudeCode` l.416.
- `adapters/opencode/__init__.py`: global, proyecto (`opencode.json[c]`) y gestionada; global/gestionada exigen opt-in (docstring l.1-8). Semántica "gana la última" (l.10-12). Esquema 1.x/2.x/ambiguo inferido por la forma de los archivos (l.119, 334-347, 388-391); no prueba la versión instalada. Sinónimos 1.x→2.x (`bash`→`shell`, l.82). Docstring declara no probado contra instalación real, se asume 2.x.
- Kit de conformidad `adapters/conformance/__init__.py`: `ejecutar_conformidad(fabrica, raiz, archivo_configuracion, clave_entorno)` (l.60) escribe configs hostiles (tubería simulada, anidamiento, 5 MB) y exige: sin excepciones, `NoRevisado` con motivo correcto, sin valor de entorno (canario `CANARIO-CONFORMIDAD-...`, l.24).
- Registro: no hay entry points. `app/auditar.py:62-73` tiene una tupla fija de detectores con los adaptadores importados directamente; `pyproject.toml` solo declara `[project.scripts] agentreach` y `requires-python >=3.12`.

## (e) CLI y app

- Entrada: `agentreach = agentreach.cli:main` (pyproject l.12-13). `_comando` (cli l.257): `audit` (implícito) o `doctor`; `agentreach RUTA` = `audit RUTA`. Códigos: 0, 1, 2 (uso/permiso), 3 (error interno), 130 (Ctrl+C) (`main`, l.441-456).
- Opciones (l.205-244): `--detalle`, `--idioma es|en|auto`, `--tono cercano|formal`, `--tema claro|oscuro|auto`, `--agente claude-code|opencode`, `--color`, `--ascii`, `--no-banner`, `--salida` (modo "x": no pisa; no dentro de la carpeta analizada), `--formato texto|html` (html exige `--salida`), `--abrir`, `--no-abrir`, `--sin-reporte-html`, `--estricto`, `--incluir-ubicaciones-sensibles`, `--tarea`, `--home`, `--ancho`. `--json` existe oculto y responde error 2 (l.235, `_ejecutar` l.646).
- `agentreach doctor` (`app/doctor.py`, cli `_doctor` l.459): 7 comprobaciones de solo lectura (Python ≥3.12, permisos, codificación, color, Unicode, idioma, ancho); falla → código 1.
- `cli/reportes.py`: `CARPETA = "AgentReach-reportes"` en la carpeta personal (l.17), fuera de la carpeta auditada y sin seguir enlaces; archivo `agentreach-AAAAMMDD-HHMMSS-<nombre>.html` creado con "x" (l.73-91); `preferencias.json` recuerda la respuesta a "¿abrir?" por carpeta (l.94-122, rechaza enlaces). Por defecto una auditoría en modo texto escribe también ese HTML (cli l.723-724). Abrir en navegador: `--abrir`, preferencia recordada, o pregunta interactiva con reintentos (`_reporte_html`, l.601-635; `infra/navegador.py`:16 `webbrowser.open`).
- Sin terminal interactiva no lee nada (código 2, `_ejecutar` l.650); además pide permiso de lectura y de reglas fuera del proyecto (`_pedir_lectura`, `_pedir_reglas`).

## DESFASES con el borrador

1. **Narrator**: el borrador (AD-10) pide puerto vacío en `core.contracts`; existe como `Protocol` vacío en `contracts/ports.py:139` con `TODO(Q10)` abierto. Coincide, sin implementación.
2. **AD-8 JSON canónico**: no existe un JSON canónico emitido por el CLI. `--json` está oculto y rechazado. El "esquema 1" solo va embebido en el HTML (`construir_datos`).
3. **Markdown**: no existe (`grep` y estructura de `reporting/`: solo texto, texto mínimo y HTML). Tampoco `json_report.py` ni `markdown_report.py` de la estructura propuesta.
4. **SARIF**: no existe (coincide con "se pospone").
5. **Texto y HTML derivan de `DatosReporte` (vistas de la compuerta), no del JSON canónico**: el principio "Markdown y texto salen del JSON" se cambió por "todo sale de las vistas de gate.py". Resultado equivalente en seguridad, distinto en forma.
6. **HTML no estaba en AD-8** y es hoy el formato principal; JSON y CSV se generan en el navegador desde el HTML (`btnJson`/`btnCsv`, plantilla l.1331-1332, Blob + `toCSV` con neutralización de fórmulas l.1306), no desde Python. El JSON exportado es `{tool, agent, findings}`, distinto del esquema 1.
7. **Entry points (AD-2 opción A)**: no implementados; el registro es en el árbol (opción B, `app/auditar.py:62-73`). `ADP_X` de terceros no existe; el kit de conformidad sí.
8. **Python mínimo**: borrador supone 3.11 (S7); el código exige ≥3.12 (`pyproject.toml:8`, `doctor.py`).
9. **Catálogo de agentes y TH-1..TH-20**: el borrador no habla de reconocer 18 agentes ni de catálogo de firmas; el catálogo vive en `data/` empaquetado y duplicado en docs (con prueba de igualdad).
10. **Narración/terminología**: el borrador no prevé tono cercano/formal, glosario de 12 fichas ni autocomprobación como paso del reporte; son añadidos de las historias 29-33.

## LÍMITES CONOCIDOS

- No ejecuté la suite de pruebas ni generé un reporte; las afirmaciones sobre pruebas se basan en grep/lectura.
- No leí por completo `plantilla_reporte.html`, `adapters/*/__init__.py` ni `texto.py`; el detalle de cada sección del reporte puede tener matices.
- Números de línea de `agentes.py` marcados con `~` son aproximados (por la lectura de fragmentos).
- Número de "firmas" del catálogo de agentes no contabilizado (la estructura no tiene un campo `firmas`).
- Compatibilidad real con opencode 1.x/2.x no comprobada contra instalaciones reales (lo declara el propio código); solo se infiere por la forma de los archivos.
- Identidad `plantilla_reporte.html` vs `docs/reporte-html/plantilla.html`: `diff -q` sin salida; no hay prueba que lo vigile que yo haya encontrado.
