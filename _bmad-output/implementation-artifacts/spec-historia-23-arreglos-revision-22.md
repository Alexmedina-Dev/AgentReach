# Historia 23: arreglos de la revisión de seguridad de la historia 22

**Estado: terminada (2026-11-10).** Fuente: `planning-artifacts/review-historia-22.md` (orden sugerido de arreglos).

| # | Hallazgo | Arreglo | Prueba |
|---|---|---|---|
| 7e | `doctor` listaba la carpeta (`os.scandir`) sin permiso | Solo pregunta permisos al sistema (`isdir` + `os.access`): no lista ni abre nada | `test_el_doctor_no_lista_ni_abre_la_carpeta` |
| 7c | `--salida` pisaba archivos existentes | Se niega si el archivo ya existe (antes de preguntar ni leer), abre con modo `x`, no sigue enlaces; igual en `doctor --salida` | `test_salida_*`, `test_doctor_salida_tampoco_pisa` |
| 7d | `preferencias.json` escrito a través de un enlace duro o simbólico | `guardar_preferencia` no escribe si es enlace o tiene más de un enlace duro | `test_la_preferencia_no_se_escribe_*` |
| 3b | La pregunta mostraba la ruta del enlace sin decir a dónde apunta | Si la ruta real difiere de la escrita, se muestra también «(ruta real: ...)» | `test_si_la_ruta_es_un_enlace_*`, `test_la_ruta_real_se_muestra_*` |
| 4c | `C:\Users` (contiene carpetas personales) sin advertencia | Advertencia también si la carpeta CONTIENE la carpeta personal | `test_una_carpeta_que_contiene_la_personal_*` |
| 1d | Ctrl+C dejaba una traza | Se captura: «Cancelado por la persona (Ctrl+C)», código 130, sin traza | `test_ctrl_c_*` |
| 5c | `isdir` antes de comprobar la terminal | Sin terminal ni se mira si la carpeta existe | `test_sin_terminal_ni_se_comprueba_*` |
| — | 3 errores de `ruff` | Ya estaban corregidos (ruff limpio) | — |

**Diferido:** M1 (confirmación desde el dispositivo de consola real; Alex: «cuando se retome»), ya en `mejoras-posteriores.md`. Sin verificar: Linux/macOS y una terminal real de Windows.
