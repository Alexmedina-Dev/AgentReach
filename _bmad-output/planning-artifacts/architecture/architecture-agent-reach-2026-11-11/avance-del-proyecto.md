# Avance de AgentReach (2026-11-11) y cómo se calcula

100 % significa **MVP terminado y ejecutado** (definición de Alex). El porcentaje mezcla tres bloques con peso distinto, para que construir mucho no tape lo que aún no se ha comprobado.

| Bloque | Peso | Qué mide | Resultado | Aporta |
|---|---|---|---|---|
| **A. Construcción** | 50 % | Historias del MVP terminadas (épicas 1 a 6 de `epics.md`, 40 historias, más la Historia 34 del README) | **39 de 41** = 95 % | 47,5 |
| **B. Verificación y cierre del MVP** | 40 % | Los 8 criterios de salida del PRD (§7.3), contando medio punto cuando se cumplen a medias | **5,1 de 8** = 64 % | 25,5 |
| **C. Listo para publicar** | 10 % | Historias de la épica 7 (M1, adaptadores de terceros, `--redact-paths`, repositorio público, etc.) | **0 de 7** = 0 % | 0 |
| **Total** | 100 % | | | **≈ 73 %** |

## Detalle del bloque B (criterios de salida del PRD)

| # | Criterio | Puntos | Por qué |
|---|---|---|---|
| 1 | Pruebas con opencode y luego con Claude Code | 0,5 | Claude Code y el oráculo pasan; falta la corrida con opencode real (1.19.0, otro equipo) |
| 2 | Cero «comprobado» falsos y todos los casos del oráculo (SM-1, SM-7) | 1,0 | El oráculo pasa (13 comprobado, 33 potencial, 2 hipótesis por agente) |
| 3 | Ningún valor de secreto en un reporte (SM-2) | 1,0 | Pruebas con canarios y reglas no negociables |
| 4 | Cada diferencia con el oráculo se explica (SM-3) | 0,5 | 22 casos aún sin verificar en fuente primaria (historia 5.6) |
| 5 | Alex verifica que funciona | 0,5 | Terminal en Orca (29, 30), HTML (19, 20, 21) hechos; faltan 32, 33 y comprobar un hallazgo con su comando |
| 6 | Prueba de la *junction* (enlace que sale del proyecto) | 1,0 | Pasa |
| 7 | Determinabilidad en configuración real medida (SM-8) | 0,0 | Sin medir |
| 8 | Pendientes manuales de Alex cerrados | 0,6 | 3 de 5 hechos; faltan un hallazgo con su comando y opencode real |
| | **Suma** | **5,1** | de 8 |

## Por qué este número es menor que el 92 % que di antes

Aquel 92 % solo contaba la **construcción** (bloque A). Este cálculo añade lo que falta **comprobar** y lo que falta para **publicar**. Si el criterio de Alex fuera solo «construido y verificado» (sin el bloque C), el avance sería 47,5 + 25,5 sobre 90 = **≈ 81 %**.

## Qué lo movería más

1. Cerrar el oráculo (5.6) y la corrida con opencode real: +≈ 3 puntos.
2. Medir SM-8 con tu configuración real: +≈ 2 puntos.
3. Las 7 historias de la épica 7: hasta +10 puntos.
