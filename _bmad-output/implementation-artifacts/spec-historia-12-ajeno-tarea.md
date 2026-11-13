---
title: 'Historia 12 - Ajeno a la tarea'
type: 'feature'
status: 'done'
---

## Resumen

`core/relacion_tarea.py` (`palabras`, `Referencia`, `clasificar`), `app/auditar.py` (`_referencia`: README con `leer_seguro`,
solo quedan palabras; parametros `tarea` y `trabajo`), flags `--tarea` y `--directorio-de-trabajo`. Reglas [SUPUESTO] (FR-9):
fuera del directorio de trabajo es ajeno; un archivo suelto en la raiz es del proyecto; dentro, coincidencia de palabras de la
ruta con la tarea y el README (singular/plural por prefijo de 4 letras); sin coincidencia y con tarea: si; solo con README o sin
nada: no determinado. El directorio de trabajo por defecto es la carpeta auditada; AJ-01 se obtiene con `--directorio-de-trabajo`
apuntando al proyecto y la raiz en la carpeta contenedora.

## Review Triage Log

### 2026-11-09 - Review pass
- Revision propia (sin subagentes: la historia es M y de logica pura; el riesgo de fuga del texto del README y de colgarse con
  un README raro se cubre con pruebas) - high 0, medium 0, low 3
- `[defer]` la regla por palabras es simple: un hallazgo con ruta de palabras comunes ("src/config") nunca coincide; un README que
  nombra todo marca todo como relacionado
- `[defer]` no se mira el nombre de la carpeta del proyecto ni el historial del chat (despues del MVP)
- `[defer]` ``--directorio-de-trabajo`` es [SUPUESTO] de nombre; si Alex prefiere deducirlo de la carpeta actual, es un cambio de una linea

## Auto Run Result

Verificacion: ver el reporte de la vuelta. Sin commit.
