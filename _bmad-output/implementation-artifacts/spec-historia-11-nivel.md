---
title: 'Historia 11 - Calculo del nivel de confianza'
type: 'feature'
status: 'done'
---

## Resumen

`core/politica.py` (base y nivel maximo por tipo, TH-1 a TH-20), `core/nivel.py` (`calcular`, tabla de FR-5 como funcion pura),
`core/invariantes.py` (`comprobar`, FR-23), `core/evaluador.py` (mide existe, permiso, regla de cada agente, confirma por la
segunda via de la Historia 18 y emite un hallazgo por agente). `app/auditar.py` lo ejecuta tras la tuberia con la sonda y el
verificador reales (los de Windows). `Finding.certeza` (completa/dudosa) y dos motivos nuevos: `no_confirmado_independiente`
y `sin_certeza_del_archivo`. `git_meta` marca como dudosos: remoto con valor de relleno o referencia (GT-08), `core.hooksPath`
(GT-05), hooks (GT-07) y lo que viene de un include (GT-13).

Reglas de Alex cumplidas: la herencia no baja el nivel; un deny/ask solo baja a potencial; la verificacion independiente que
discrepa o no puede baja a potencial; un tipo reconocido por nombre (TH-17) sin fuente verificada no pasa de potencial.

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: 20 findings (ciega 10, casos limite 10) - high 4, medium 8, low 8, false 0
- `[high]` `[patch]` carpeta relativa degradaba todo a potencial (la sonda solo mide rutas absolutas) - `auditar` usa ruta absoluta
- `[high]` `[patch]` un adaptador que lanza o devuelve algo que no es una postura dejaba pasar a comprobado un hecho de los bytes y perdia un deny - la postura debe ser conocida (allow o sin regla) y se separan los dos intentos
- `[high]` `[patch]` includes (GT-13) y `includeIf` salian comprobados - lo que viene de otro archivo es dudoso
- `[medium]` `[patch]` confirmacion contra otra medicion que la del nivel - se compara contra el permiso ya medido; cache por ruta normalizada
- `[medium]` `[patch]` TH-12 y TH-13 bajaban por la regla de LEER (opencode `external_directory`) - se evaluan una vez, sin regla de lectura (AT-10)
- `[medium]` `[patch]` URL con referencia (`${TOKEN}`) contaba como clave literal; `.git` ilegible perdia su no revisado; postura del candidato pisada sin adaptador; adaptadores duplicados por plataforma; `SondaPosix` no marcaba enlaces ni root
- `[defer]` configuracion de Claude Code ilegible cuenta como "sin regla" (queda en `no_revisados`, pero el nivel no baja); mismo riesgo en opencode (no se toca hasta la 10b)
- `[defer]` GT-09 (formato retorcido) sale comprobado y el oraculo dice potencial: falta que el lector de git marque continuacion de linea y mayusculas (pregunta 27)
- `[defer]` sin verificador en POSIX no hay segunda via (FR-24): hoy no baja el nivel; decidir con Alex si debe bajar
- `[defer]` ruta real del archivo en `Finding` (nombres con caracteres ocultos miden otro archivo): lo trae la Historia 13; motivo "tope del tipo" propio; `certeza` en `a_dict`; no emitir agentes sin configuracion
- `[reject]` TH-1 de PP-01a a PP-01f comprobado en opencode (lo avala el oraculo); GT-17 y GT-18 comprobados (el oraculo los cambio el 2026-11-09)

## Auto Run Result

Verificacion: 832 pasan / 13 omitidas con el proyecto de prueba; ruff limpio. Sin commit.
