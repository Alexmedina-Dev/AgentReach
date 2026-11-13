# Historia 25: por qué un nivel es «no determinado»

**Estado: terminada (2026-11-10).** Origen: la prueba real de Alex (con su `~/.claude/settings.json` con hooks `PreToolUse`, los 17 hallazgos de Claude Code salían potencial por `funcion_no_modelada`, sin decir por qué).

## Qué dice ahora
El archivo y la CLAVE de configuración que AgentReach no interpreta, **sin valores**: p. ej. `~/.claude/settings.json · hooks.PreToolUse`.
- **Datos:** `NoRevisado.clave` (limpia y acotada a 80); cada adaptador deja `causas_no_determinado`. Claves de Claude Code: `hooks.PreToolUse`, `sandbox`, `allowManagedPermissionRulesOnly`, `permissions.<allow|ask|deny>` (patrón `Read` que no se interpreta). De opencode: `tools`, `mode`, `plugin(s)`, `experimental.policies`, `agent(s).*.permission(s)`/`tools`, la clave de un encabezado de agente `.md`, y el NOMBRE de una clave repetida. Los nombres salen de una lista fija (nunca texto del archivo), salvo la clave repetida.
- **Terminal:** sección «POR QUÉ HAY NIVELES "NO DETERMINADO"» (corto y completo, ES/EN) con archivo · clave, el motivo y cómo resolverlo.
- **HTML:** `agents[].not_determined` en el esquema; el «por qué» de cada hallazgo no determinado lleva archivo · clave, y un aviso en el resumen.
- **JSON y CSV exportados desde el reporte:** campo `not_determined_by` y el `why` con la causa.

## Pruebas
`tests/test_historia_25.py` (18, incluida una en el navegador con descargas reales del JSON y el CSV). Sin valores: un comando de hook con un marcador no sale en ningún formato.
