# Historia 21: uso diario (carpeta actual, banner, reporte HTML y navegador)

**Estado: terminada (2026-11-10).**

## Qué cambió
1. **Sin ruta** (`agentreach`): revisa la carpeta actual. Si es la carpeta personal o la raíz de un disco, pregunta antes («¿Continuar? (s/N)»); sin terminal (tubería, CI) no hay a quién preguntar y sale con código 2 pidiendo una ruta. Con ruta explícita no pregunta.
2. **Banner mediano** (en vez del mínimo) al revisar y en `doctor`, con **una línea en blanco antes**. Solo en terminal interactiva (como antes).
3. **Reporte HTML automático** en `<carpeta personal>/AgentReach-reportes/agentreach-AAAAMMDD-HHMMSS-<carpeta>.html` (nunca pisa uno anterior). La terminal dice dónde quedó y qué se verá (resumen por nivel, lista de hallazgos y tabla); en una tubería el aviso va a stderr. Si esa carpeta cayera dentro de la revisada, o fuera un enlace, no se crea y se dice por qué (aviso en stderr; el código de salida no cambia). `--salida` y `--formato html --salida` siguen igual; `--sin-reporte-html` lo apaga.
4. **«¿Abrir el reporte en el navegador? (s/N)»**: se pregunta una vez (solo con terminal) y la respuesta se recuerda en `AgentReach-reportes/preferencias.json`. `--abrir` abre sin preguntar (no recuerda nada); `--no-abrir` ni pregunta ni abre. Una entrada cerrada cuenta como «no».
5. **`--help`** muestra el banner grande (ya lo hacía en una terminal interactiva; ahora hay prueba).
6. **Reglas de solo lectura precisadas** (PRD FR-1, `CONTRIBUTING.md`): dentro de lo revisado nada; fuera, solo `--salida` y `AgentReach-reportes`; durante la revisión ningún programa; al terminar, solo abrir el HTML local con el navegador y con permiso. Pruebas: vigilancia de escritura con carpeta permitida (`escritura_solo_en`), `webbrowser` solo en `infra/navegador.py` y llamado solo desde `_reporte_html`, `makedirs` solo en `cli/reportes.py`.

## Decisiones para Alex
- **Excepción a «no ejecuta programas»:** abrir el navegador le pide algo al sistema (`webbrowser.open`, con `file://`). Es solo después de revisar y con permiso, pero es una excepción a la letra de FR-1.
- **Sin terminal:** se crea el HTML igual (aviso a stderr) pero nunca se pregunta ni se abre solo.
- **Revisar la carpeta personal completa:** el HTML no se crea (la carpeta de reportes quedaría dentro); con `--salida` se elige una ruta de fuera.
- Flags nuevos además de `--abrir`: `--no-abrir` y `--sin-reporte-html`.

## Pruebas
`tests/test_historia_21.py` (37), `tests/reglas_no_negociables/test_reportes_y_navegador.py` (7); ajustadas las de banner, CLI sin ruta y reglas de escritura. Verificadas con mutaciones (quitar la comprobación «dentro» y quitar la condición de terminal rompen pruebas).

## No verificado
- Abrir el navegador de verdad (las pruebas lo reemplazan por un registro).
- `--help` y la pregunta en una terminal real de Windows (las pruebas simulan la terminal).
