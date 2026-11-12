---
title: 'Historia 13 - Reporte completo: ocho campos, idiomas, autocomprobacion y codigo de salida'
type: 'feature'
status: 'done'
---

## Resumen

Contenido: `reporting/gate.py` (compuerta con vistas de lista blanca y `preparar`), `reporting/texto.py` (estructura y
catalogos), `reporting/limpieza.py` (nombres peligrosos escritos), `core/autocomprobacion.py` (invariantes + reabrir cada
archivo citado), `core/catalogo_explicaciones.py` (titulos, motivos, limites FR-21, nombres), textos del catalogo reescritos
en tono de tu con las palabras explicadas. Comando: `agentreach audit RUTA` y atajo `agentreach RUTA`, opciones `--detalle`,
`--idioma`, `--color`, `--ascii`, `--salida`, `--estricto`, `--ancho`, `--tarea`, `--directorio-de-trabajo`; codigos 0, 1, 2 y 3.
Contrato: `Location.ruta_real` y `NoRevisado.ruta_real` (la ruta antes de limpiar, solo para reabrir; no se imprime ni sale en
`repr`), `Finding.certeza`, `RutaReal`. `Evaluador` conserva con que hechos calculo cada nivel para la autocomprobacion.

Cambios a historias terminadas (se avisa): 5b (el reporte provisional `texto_minimo` ya no lo usa el comando; 5 pruebas
actualizadas), 12 (carpetas `.git`, `.claude`... no son ajenas) y `test_contratos` (acepta `RutaReal`).

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: 26 findings (ciega 14, casos limite 12) - high 2, medium 14, low 10, false 0
- `[high]` `[patch]` el nombre de la herramienta de una regla (clave de un archivo) se imprimia sin escribir; el recorrido perdia sus `no_revisados` (carpetas ilegibles, profundidad)
- `[medium]` `[patch]` `--salida` (enlaces duros, rutas con `..`), errores fuera del `try` daban traza y codigo 1 (ahora 3), rutas con espacios partidas por el ajuste, `--ascii` dejaba tildes y `·`, consola sin simbolos unificaba los niveles (ahora ASCII automatico), "igual que la linea ?", clave de agrupacion sin `ajeno`, `~` del proyecto confundido con la carpeta personal, barra invertida en POSIX, correcciones contadas por hallazgo, patron de nombres alineado con el detector, avisos con identificadores sin `--detalle`, errores de argparse en el idioma elegido, sin carpeta da 2, tuberia cerrada
- `[defer]` rutas seudo-archivo ("(Windows nativo)") en espanol sin traducir; TH-10 dice solo "No determinado"; agrupar por mayusculas sin distinguir; `linea_contiene_clave` solo comprueba credenciales y git (el resto confirma cualquier linea no vacia); `sin_reglas` sin usar; tests de locale solo con funcion falsa
- `[reject]` dividir en dos historias (la 13 cierra completa; el ancho, color y codificacion siguen siendo la 13b)

## Auto Run Result

Verificacion: 915 pasan / 15 omitidas con el proyecto de prueba; 877 / 53 sin el. Ruff limpio. Sin commit.
