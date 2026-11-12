---
title: 'Historia 13b - Reporte de terminal: ancho, color, codificacion y limpieza al imprimir'
type: 'feature'
status: 'done'
---

## Resumen

`reporting/formato.py` (ancho visible con caracteres anchos, `ajustar` por palabras con sangria francesa, `decidir_color` con la
prioridad del diseno, paleta A de 24 bits / 16 colores / variante de fondo claro por `COLORFGBG`, `pintar`, `activar_vt` con
ctypes, `ultima_comprobacion`, `preparar_salida`), `reporting/limpieza.py` (segunda barrera idempotente), `reporting/texto.py`
(roles de color aplicados DESPUES de ajustar, rutas como fichas indivisibles, simbolos ASCII o Unicode, nota de nombres escritos
decidida al final), `cli/__init__.py` (color, terminal o no, UTF-8 en redirecciones, `--salida` sin color, tuberias cerradas).
Salida no terminal: UTF-8 con simbolos ASCII; `--ascii` quita tambien las tildes; terminal que no soporta los simbolos: ASCII.

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: 10 findings (un revisor independiente) - high 0, medium 7, low 3, false 0
- `[medium]` `[patch]` la segunda barrera recortaba dos veces (marca con cifra equivocada); rutas con espacios dentro de una frase se partian (ahora son fichas); `Ubicacion:` y la carpeta del encabezado sin ajustar (ahora la ruta entera va en su linea); `activar_vt` podia lanzar `ArgumentError` (ahora `argtypes` y captura general); `ultima_comprobacion` dejaba pasar `ESC[31m` ajenos, BEL y controles de 8 bits (ahora solo las formas que emite `pintar`); la prueba de importar pasaba por casualidad (ahora espia `reconfigure`); una tuberia cerrada se probaba sin flujo real (ahora subproceso) y un `OSError` que no es de tuberia se tragaba (ahora es error interno)
- `[low]` `[patch]` nota de nombres escritos tambien por `h.regla` y `h.agente`; el mensaje de argumentos mal escribe los caracteres peligrosos
- `[defer]` un archivo con la secuencia literal `\x1b` en su nombre se ve igual que uno con ESC real (la barra invertida no se escribe): limite declarado
- `[defer]` (h) revision de Alex a mano de las cuatro muestras en su consola y en una de fondo claro; las muestras de `docs/reporte-terminal/muestras/` no se regeneraron

## Auto Run Result

Verificacion: 966 pasan / 15 omitidas con el proyecto de prueba; 928 / 53 sin el. Ruff limpio. Sin commit.
