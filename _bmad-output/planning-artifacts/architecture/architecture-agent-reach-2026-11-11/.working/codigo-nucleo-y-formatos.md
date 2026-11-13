# Contraste borrador (2026-11-06) vs código: núcleo, registro, datos, formatos, carpetas

Rutas relativas a `src/agentreach/` salvo indicación. Comprobado con lectura y grep; no se ejecutaron pruebas.

| Decisión del borrador | Qué hace el código (archivo:línea) | ¿Coincide? | Nota |
|---|---|---|---|
| AD-1 hexagonal, hallazgo como contrato | `contracts/finding.py:543` `Finding` congelado con 11 campos. `core/pipeline.py:1-12` solo conoce `contracts` | Sí | `Finding` ya no tiene "ocho campos" (`tests/test_contratos.py:72`); `regla` y `certeza` se añadieron después |
| Regla de dependencias: core no importa adapters/infra/reporting | grep de imports en `core/` y `contracts/`: 0 coincidencias. Lo vigila `tests/test_contratos.py:164-180` (AST, incluye imports relativos; prohíbe `adapters`, `infra`, `reporting`) | Sí | No vigila `collectors` ni que `contracts` no importe `core` |
| Pipeline | `core/pipeline.py`: `Pipeline(detectores).ejecutar(proyecto)` reúne y `ordenar()`; si un detector falla lanza `RuntimeError` con su nombre (:42-45). `app/auditar.py:128` lo usa y :131 crea `Evaluador` | Parcial | El borrador propone `reachability.py` y `taxonomy.py`; el código tiene `evaluador.py`, `nivel.py`, `politica.py`, `invariantes.py`, `relacion_tarea.py`, `verificacion_independiente.py`, `autocomprobacion.py`, `catalogo_*` |
| Puertos ReadOnlyFs, EnvView, FsProbe, AgentAdapter, Narrator | `contracts/ports.py`: `ReadOnlyFs` (~:90), `EnvView`, `FsProbe`, `AgentAdapter` (:121), `Narrator` (:139, Protocol sin métodos; TODO(Q10) en :18). Además `Detector` (:131), `Capacidad`, `PermisoLectura`, `Metadatos`, `PermisosArchivo` | Sí (+extra) | `Detector` no está en el borrador. `ReadOnlyFs` tiene solo `listar`, `metadatos`, `leer_texto` |
| AD-2 registro por entry points (A) + árbol (B) para el de referencia | Sin `importlib.metadata` ni `entry_points` en ningún `.py` (grep). `pyproject.toml` solo define `[project.scripts]`. `adapters/__init__.py` solo docstring + TODO(Q9). El registro es una tupla de lambdas `_detectores` en `app/auditar.py:61-73`, con `AdaptadorClaudeCode` y `AdaptadorOpencode` importados directo (:17-18) | Parcial | Solo se cumple B, y cableada. La parte A (terceros) no existe |
| Adaptador de referencia en el árbol | `adapters/claude_code/` (`__init__`, `catalogo.py`, `reglas.py`), `adapters/opencode/__init__.py`, `adapters/base.py` (Protocol `AdaptadorBase`: `cargar`, `postura_para`, `regla_para`; `ResultadoAdaptador` :54) | Sí (+extra) | Existe un segundo adaptador (opencode) y `base.py`, ausentes de la sección 7. TODO(Q9) en `adapters/__init__.py:3` sigue "abierto" aunque ya está implementado |
| Kit de conformidad | `adapters/conformance/__init__.py` (102 líneas): `ejecutar_conformidad(fabrica, tmp, archivo_configuracion, clave_entorno)` escribe configs hostiles y comprueba que no lance excepción, que informe `NoRevisado` con motivo correcto y que no deje valores de entorno (docstring :1-12; `CANARIO` :23). Importa `infra.fs_solo_lectura` (:20) | Sí | Comprueba 3 propiedades; no verifica la "capacidad declarada" de la sección 8 |
| AD-7 dataclasses congeladas, sin Pydantic | `@dataclass(frozen=True, slots=True)` en `contracts/finding.py:237,543`, `adapters/base.py:24,35,46,54`, `contracts/ports.py`. Pydantic: 0 coincidencias. `pyproject.toml:7` `dependencies = []` | Sí | Además con `slots` |
| AD-7 JSON Schema generado y comprobado en pruebas | No existe `contracts/schema/finding.schema.json` (`contracts/` tiene finding, no_revisado, ports, rutas). El único esquema es `docs/reporte-html/esquema-datos.schema.json`, cargado en `tests/test_reporte_html.py:47`; describe los datos del HTML, no `Finding` | No | Escrito a mano y para el HTML |
| AD-7 Python mínimo 3.11 (S7) | `pyproject.toml:6` `requires-python = ">=3.12"`; ruff `target-version = "py312"`; README badge 3.12+. `tomllib` en `config/__init__.py:11` | No | Mínimo real 3.12. Ejecución solo stdlib; dev: `pytest>=8`, `ruff>=0.6`; build `uv_build>=0.13.7,<0.14` |
| AD-8 JSON canónico + Markdown + texto | `cli/__init__.py:237` `--formato` con choices `("texto","html")`. `reporting/`: `texto.py`, `texto_minimo.py`, `html.py`, `gate.py`, `formato.py`, `marca.py`, `limpieza.py`. Sin `json_report.py` ni `markdown_report.py`. Grep de sarif/csv/markdown: nada | No | Salidas reales: terminal y HTML estático (exige `--salida`, `cli/__init__.py:655`). `json.dumps` solo incrusta datos en el HTML (`html.py:221`). `Finding.a_dict` existe (`finding.py:260,587`) pero no hay salida JSON por CLI (uso fuera de pruebas: sin comprobar) |
| AD-8 SARIF pospuesto | No existe | Sí | Coherente |
| Compuerta de salida con lista blanca | `reporting/gate.py`: `preparar` (:173), `HallazgoVista`, `DatosReporte`, `codigo_de_salida` (:166), `ruta_visible` (:145); `html.py:38` importa de `gate` | Sí | |
| AD-10 Narrator vacío | `contracts/ports.py:138-141`, exportado en `contracts/__init__.py:39,67`; docstring "Vacío a propósito en el MVP (FR-11)" | Sí | Vive en `contracts.ports`, no en `core.contracts` |
| S7 colectores | Reales: `archivos_repo`, `git_meta`, `entorno`, `contexto`, `ubicaciones_usuario`, más `config_ejecuta_sola`, `despliegue`, `enlaces`, `instrucciones_fuera`, `invisibles`, `detector/{archivos,patrones}` | Parcial | Nombres en español; 6 colectores no previstos |
| S7 infra | Reales: `fs_solo_lectura`, `env_view`, `sonda_windows`, `sonda_posix`, más `verificador_permiso_windows`, `lectura_segura`, `localizador`, `navegador`, `lector_config_git`, `json_con_comentarios` | Parcial | `navegador` (abre el HTML) y otros no previstos |
| S7 `config/` TOML | `config/__init__.py`, único módulo, `tomllib` (:11,78) | Sí | |
| S7 `app/` audit, list-adapters | `app/auditar.py`, `app/agentes.py`, `app/doctor.py`; no hay list-adapters | Parcial | |
| S7 `cli/` argparse | `cli/__init__.py` (argparse; códigos 0-3, docstring :3-4), `cli/reportes.py` | Sí | |
| S7 `data/` | `data/catalogo-agentes.json` | No (extra) | No está en el borrador |
| S7 `core/` extras | `core/catalogo_terminos.py`, `core/catalogo_explicaciones.py`; `reporting/marca.py`, `reporting/formato.py` | No (extra) | Capas de explicación y marca nacidas en historias 29-33 |
| S7 tests unit/contract/e2e/property | `tests/` plano con ~45 `test_*.py`, `tests/oraculo/{expected.json,test_oraculo.py}`, `tests/reglas_no_negociables/` (solo lectura, sin red, sin ejecutar programas, sin valores de secretos, límites duros). Sin subcarpetas unit/contract/e2e/property | Parcial | Oráculo y reglas bloqueantes sí; jerarquía propuesta no. Pruebas de propiedades: no encontradas |
| Canario | `tests/test_contratos.py:263`; `adapters/conformance` `CANARIO` | Sí | |

## DESFASES

1. AD-2: no hay entry points; el registro es una tupla fija de lambdas en `app/auditar.py:61-73`. La vía pública para terceros no existe.
2. AD-7: Python mínimo es 3.12 (`pyproject.toml:6`), no 3.11 (S7).
3. AD-7: no hay `contracts/schema/finding.schema.json`; el único JSON Schema es de los datos del HTML, escrito a mano (`docs/reporte-html/esquema-datos.schema.json`).
4. AD-8: no hay salidas JSON ni Markdown por CLI; `--formato` admite `texto` y `html` (`cli/__init__.py:237`). El HTML no figura como formato en el borrador.
5. Sección 7: nombres de módulos en español y distintos; faltan `core/reachability.py` y `core/taxonomy.py` (lógica repartida en `evaluador`, `nivel`, `politica`).
6. Sección 7: módulos y carpetas no previstos: `adapters/base.py`, `adapters/opencode/`, `data/`, `core/catalogo_*`, `reporting/{marca,formato,limpieza,texto_minimo}`, varios colectores, `app/{agentes,doctor}`, `infra/navegador`.
7. `Finding` tiene 11 campos (no 8); `Narrator` y el puerto extra `Detector` viven en `contracts/ports.py`; `AdaptadorBase` (`adapters/base.py`) añade `cargar`/`regla_para` al puerto `AgentAdapter`.
8. Tests: estructura plana, no `unit/contract/e2e/property`; no se halló prueba basada en propiedades.
9. TODO(Q9) en `adapters/__init__.py:3` y TODO(Q7)/(Q10) en `ports.py:18-19` siguen como "abiertos" aunque opencode está implementado y Narrator existe vacío.

Sin comprobar: uso real de `Finding.a_dict` fuera de pruebas; contenido completo de `Evaluador`; existencia de pruebas de propiedades fuera de lo buscado con grep.
