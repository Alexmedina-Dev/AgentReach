---
title: 'Historia 13c - Presentacion de marca: banner, doctor, tema y tono'
type: 'feature'
status: 'done'
---

## Resumen

`reporting/marca.py` (banner grande, mediano y minimo con respaldo ASCII; AGENT #EAF4F2 y REACH #3DF5D0; solo en una terminal
interactiva), `app/doctor.py` (7 comprobaciones de solo lectura, 4 combinaciones de texto, codigo 0 o 1), `reporting/formato.py`
(`resolver_tema`, variante clara tambien en 16 colores, roles de marca), `core/catalogo_explicaciones.py` (`Tono`, textos
formales), `reporting/texto.py` (una seccion por agente sin mezclar niveles, tono formal), `cli/__init__.py` (`doctor`,
`--tema`, `--tono`, `--agente`, `--no-banner`, `--json` que aun no existe y da 2, `--version` en una linea `agentreach X.Y.Z`).
Decisiones mias donde el diseno y la historia chocan (la historia manda): tono cercano por defecto; `--version` sin banner;
una falla del doctor es lo que impide leer el reporte (Python < 3.12, carpeta sin permiso, consola sin tildes ni simbolos, terminal
de Windows que no activo los colores); un "sin color" elegido (NO_COLOR, redireccion, `--color nunca`) es un aviso.
`--version` muestra el nucleo numerico (`0.1.0`) aunque el paquete diga `0.1.0.dev0`.

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: 13 findings (un revisor independiente) - high 1, medium 6, low 4, tests 2, false 0
- `[high]` `[patch]` `agentreach` sin carpeta y `--help` ignoraban `--ascii`, `--color`, `--tema` y `--no-banner`
- `[medium]` `[patch]` 16 colores sin variante clara (blanco sobre blanco con `COLORFGBG`); `doctor` ignoraba `--salida`; las opciones antes de `doctor` lo rompian; el tamano del banner no seguia el ancho real; `--agente` dejaba correcciones del otro agente
- `[low]` `[patch]` motivo real de "sin color"; `--tema auto` y valor invalido; `getcwd` y codificacion vacia; `--help` con consola ASCII; `AGENTREACH_NO_BANNER` con cualquier valor
- `[patch]` pruebas: aserciones vacias, `or True`, `readouterr` doble y casos sin cubrir (ayuda, doctor con salida, anchos, 16 colores claros)
- `[defer]` `--agente` no filtra "no se pudo revisar" ni "archivos mirados" (sin plataforma de origen en `NoRevisado`)
- `[defer]` el alto de la terminal no se mira para elegir el banner; (h) del reporte y las muestras: revision de Alex a mano en su consola

## Auto Run Result

Verificacion: 1010 pasan / 15 omitidas con el proyecto de prueba; 971 / 54 sin el. Ruff limpio. Sin commit.
