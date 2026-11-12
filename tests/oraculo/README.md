# Evaluación contra el oráculo (Historia 15)

Compara lo que AgentReach reporta con `respuestas-esperadas.md` (el oráculo del proyecto de prueba) caso por caso.

## Cómo se corre

```powershell
$env:AGENTREACH_PROYECTO_PRUEBA = "C:\dev\proyecto-prueba-agentreach"
uv run pytest tests/oraculo -q
```

Sin la variable, las pruebas se saltan; con `CI` o `AGENTREACH_EXIGIR_PRUEBAS` definidas, **fallan** (no se pueden saltar en silencio).
La evaluación audita solo en lectura, sin red y sin ejecutar nada. Las raíces que usa:

| `raiz` en `expected.json` | Qué se audita |
|---|---|
| `proyecto` | `proyecto/` con el opt-in de ubicaciones sensibles apuntando a `home-falso/` |
| `contenedora` | la carpeta contenedora, con el directorio de trabajo en `proyecto/` (AJ-01) |
| `opencode-sin-read` | `proyecto-opencode-sin-read/` (OC-01) |
| `trampas-git/<caso>` | cada trampa de git, sin opt-in |
| `entorno` | `proyecto/` con `AGENTREACH_PRUEBA_API_TOKEN` y `AGENTREACH_PRUEBA_DB_PASSWORD` solo mientras corre (EV-01) |

El entorno de la máquina se filtra (se quitan las variables con nombre de credencial): cada equipo tiene las suyas y no deben contar.

## `expected.json`

Una entrada por caso (67). Campos: `id`, `raiz`, `rutas` (sufijos de ruta), `tipos` (TH-n), `esperado`, y opcionales `linea`, `motivo`,
`solo_windows`, `con_opt_in`, `aceptado` + `explicacion` (una diferencia conocida y explicada con evidencia), `fuente_primaria` y
`confirmado_por`. `esperado` es un nivel (`comprobado`, `potencial`, `hipotesis`), `no_se_reporta`, `no_se_pudo_revisar`,
`no_aplicable`, `no_debe_existir`, o un objeto por agente (`claude-code`, `opencode`). Se derivó a mano de la tabla del oráculo y de
su sección «Niveles por agente»; una prueba comprueba que los IDs son exactamente los del oráculo y que las cifras
(18 comprobado, 28 potencial, 2 hipótesis por agente; 16 «no se reporta») coinciden.

Clasificación por caso y agente: **coincide**, **falso positivo** (hay hallazgo donde no debe, o con un nivel más alto: un
«comprobado» falso), **omisión** (falta el hallazgo, o con un nivel más bajo) o **no aplicable**.

## Confirmación desde la fuente primaria (FR-24, pregunta 22 del PRD)

**Cerrada el 2026-11-10**: un agente independiente (sin acceso a `src/` ni al nivel esperado) confirmó los 67 casos; ver
`docs/oraculo-confirmacion/confirmacion.md`. `fuente_primaria`, `confirmado_por` y `verificado_en_fuente` están llenos en `expected.json`
y la prueba ya no es `xfail`. Los casos con `verificado_en_fuente: false` (22) quedan declarados sin verificar; los que dicen
«regla del PRD» no tienen fuente externa. Diferencias con el oráculo: ver `nota_confirmacion` (AJ-01 en Claude Code sigue pendiente de decisión de Alex).

## Cómo regenerar el proyecto de prueba

`python pruebas\generar_proyecto_prueba.py` (en la carpeta del proyecto de prueba). Para EV-01 se puede lanzar el auditor con
`--con-entorno` (las variables viven solo mientras corre); aquí la prueba las pone ella misma.

## Pendiente a mano (de Alex)

Verificar uno de los hallazgos con el comando que el reporte le da, y correr la evaluación con opencode real (no está instalado en
este equipo). El segundo proyecto de prueba, hecho por otra persona, queda fuera (riesgo de sesgo del oráculo).
