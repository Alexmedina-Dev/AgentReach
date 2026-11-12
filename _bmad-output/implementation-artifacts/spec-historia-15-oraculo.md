---
title: 'Historia 15 - Evaluacion contra los 67 casos del proyecto de prueba'
type: 'feature'
status: 'done'
---

## Resumen

`tests/oraculo/expected.json` (67 casos derivados de `respuestas-esperadas.md` y su seccion "Niveles por agente"),
`tests/oraculo/test_oraculo.py` (clasifica cada caso y agente como coincide / falso positivo / omision / no aplicable; 76 pruebas
pasan; 0 "comprobado" falsos, 0 omisiones de comprobados, 0 reportes de los 16 "no se reporta", GT-02 en "no se pudo revisar", TR-01,
0 marcadores canario en la salida con opencode y luego con Claude Code, 0 discrepancias del segundo calculo del permiso en los
comprobados) y `tests/oraculo/README.md`. El entorno de la maquina se filtra para que sus variables no cuenten.

## Diferencias que la evaluacion encontro en el PRODUCTO (corregidas)

- `~/.npmrc` salia comprobado (solo se miran metadatos): ahora potencial (HF-05), `certeza` dudosa en las ubicaciones del usuario.
- EV-01: el detector de entorno no estaba registrado en `auditar` y TH-4 estaba como potencial: ahora registrado y TH-4 es hipotesis.
- GT-09 salia comprobado: el lector de git marca `peculiar` (seccion en mayusculas, clave `FsMonitor`/`FSMONITOR`, valor con continuacion
  de linea) y el hallazgo queda en potencial; `sshCommand` y `hooksPath` (camelCase normal) no cuentan como peculiares.

## Diferencias del ORACULO (explicadas en `expected.json`, para que Alex decida)

- OC-01 en Claude Code: el oraculo dice potencial; sin reglas de Claude Code el archivo es legible y FR-5 da comprobado (el potencial es el de opencode).
- PP-01a a PP-01f en opencode: las cifras del oraculo (18/28) solo cuadran si son potencial por "sin fuente verificada" (FR-7), pero su tabla por agente da PP-01 y PP-05 (mismo tipo, GITHUB_TOKEN) comprobado. AgentReach aplica la tabla por agente.
- El resumen del oraculo suma 66 (48+16+1+1) y no 67: falta EN-03 (no aplicable).

## Confirmacion desde la fuente primaria (FR-24, pregunta 22): cerrada el 2026-11-10

Un agente independiente, sin acceso a `src/` ni al nivel esperado, confirmo los 67 casos por agente (`docs/oraculo-confirmacion/confirmacion.md` y `.json`, commit c2a37ad). `expected.json` ya lleva `fuente_primaria`, `confirmado_por` y `verificado_en_fuente` en cada caso, y se quito el `xfail`.

- 45 casos verificados en fuente primaria; 22 sin verificar (los 10 sin fuente externa dicen "regla del PRD (sin fuente primaria externa)": CA-05, GT-02, GT-03, CX-02, AT-01, AT-03, AT-08, GT-08, AT-09, AT-10).
- Sin conflicto con el oraculo: opt-in de HF-01/03/05 y AT-03/10 (mismo nivel con opt-in), TR-01, y las columnas "no aplicable" del otro agente (el oraculo da una sola columna de referencia).
- EN-02: sin conflicto real, FR-19/FR-26 ponen "no se pudo revisar" en el enlace (EN-01), no en ese archivo.
- **AJ-01 en Claude Code: difiere.** Confirmacion = potencial (aviso por defecto al leer fuera del directorio, no una regla ask escrita); oraculo = comprobado. Se conserva el oraculo; decision de Alex.
- PP-01a a PP-01f: la confirmacion da potencial en ambos agentes, igual que el oraculo; AgentReach sigue en comprobado en opencode (`aceptado`), decision de Alex.
- Limite: la doc de opencode se consulto solo en 2.x; las reglas 1.x (1.19 de Alex) quedan sin verificar.
- Sigue a mano de Alex: verificar un hallazgo con el comando del reporte y correr con opencode real.

## Review Triage Log

### 2026-11-10 - Review pass
- Revision ciega de datos (un revisor sin acceso al codigo): 6 discrepancias, 0 high; GT-06 y GT-13 con rutas literales del oraculo `[patch]`; AT-04 apunta a la linea de apertura de `hooks` `[defer]`; las inconsistencias del oraculo arriba `[defer]` (decision de Alex)
- `[defer]` no hay revision independiente del codigo nuevo de esta historia (lector de git y detectores): la cubren las pruebas del oraculo

## Auto Run Result

Verificacion: 1284 pasan / 15 omitidas (suite completa con el proyecto de prueba; oraculo: 77 pasan, sin xfail). Ruff limpio. Sin commit.
