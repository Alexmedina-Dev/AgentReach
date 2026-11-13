# Que publican los repos de referencia (lectura el 2026-11-09)

Fuente: API publica de GitHub y archivos crudos. No se clono ni ejecuto nada.

## Por repositorio
- BMAD-METHOD: raiz con AGENTS.md, CHANGELOG, CONTRIBUTING, CONTRIBUTORS, LICENSE, README, SECURITY, TRADEMARK, docs/, docs-site/, skills/, tools/, .github/ (CODE_OF_CONDUCT, plantillas de issues y PR, FUNDING). NO publica _bmad-output ni .claude: su .gitignore los excluye (.claude, .agents, .cursor, .opencode, CLAUDE.local.md, .mcp.json, _bmad, _bmad-output, "por maquina, nunca se suben"). Seguridad: SECURITY.md, canal privado (aviso privado de GitHub, correo, mensaje directo); sin recompensa, da credito.
- gentle-ai: publica .claude/ (solo un archivo de bloqueo, probablemente colado), AGENTS.md, PRD.md, PRD-AGENT-BUILDER.md, docs/ con ~46 entradas (arquitectura, modelo de amenazas, auditorias, evidencia), AI_POLICY, CONTRIBUTING, TRADEMARKS, plantillas. node_modules/ y results.json estan en la raiz (higiene dudosa). Su .gitignore solo excluye .atl/, .pi/ y la base local de engram. SECURITY.md NO aparece en la raiz (no vi si esta en .github/).
- engram: publica .agents/plugins, .claude-plugin/, .engram/ (chunks, config, manifest: memoria sincronizada A PROPOSITO, solo se ignora engram.db y cloud.json), AGENTS.md, CHANGELOG, CODEOWNERS, CONTRIBUTING, DOCS.md, SECURITY.md, TRADEMARKS. .gitignore: bases *.db, exportaciones, enlaces de skills generados. Seguridad: aviso privado de GitHub; 48 h para acusar recibo; "no abras issue publico".
- cloudflare/security-audit-skill: minimo. Solo LICENSE (MIT), README y skills/ (SKILL.md, guias por fase, clases de ataque, esquema JSON, validadores con pruebas). Sin SECURITY, CONTRIBUTING ni .gitignore visible; solo un correo para consultas.

## Patrones comunes
- Los 4 publican la herramienta (skills/) y README + LICENSE. 3 de 4 tienen SECURITY.md con canal privado y CONTRIBUTING.
- AGENTS.md (instrucciones para agentes de IA) lo publican 3; CLAUDE.md ninguno.
- Planeacion/memoria personal: solo BMAD la excluye explicitamente; gentle-ai publica PRD y docs de diseno; engram publica memoria por decision propia.
- Sin ver: contenido de docs/ de BMAD y engram, licencias de terceros (ninguno en la raiz), CODE_OF_CONDUCT de los demas, si gentle-ai tiene SECURITY en .github/.

## Recomendacion para AgentReach
| Elemento | Decision | Motivo |
|---|---|---|
| Codigo, tests, LICENSE, README | Incluir | Base de los 4 |
| SECURITY.md con canal privado | Incluir | Es una herramienta de seguridad; 3 de 4 lo tienen |
| CONTRIBUTING, plantillas de issues/PR, CHANGELOG | Incluir | Estandar en BMAD y engram |
| AVISOS de terceros (licencias de dependencias) | Incluir | Ninguno lo hace; ventaja y cumplimiento |
| CODE_OF_CONDUCT | Decidir | Solo BMAD; util si habra comunidad |
| AGENTS.md | Decidir | Comun, pero revisar que no filtre rutas ni notas internas |
| docs/ de arquitectura y modelo de amenazas | Decidir | gentle-ai lo publica; publicar version limpia, no borradores |
| .claude/, .cursor/, .opencode/, CLAUDE.local.md, .mcp.json | No incluir | Config local; BMAD lo ignora; gentle-ai filtro un archivo |
| _bmad/, _bmad-output/ (PRD, planeacion, investigaciones) | No incluir | BMAD lo excluye; contiene decisiones y notas internas |
| Memoria y notas de sesion (memory, .engram, *.db) | No incluir | Pueden tener datos sensibles |
| node_modules, results.json, locks, archivos generados | No incluir | Mala higiene vista en gentle-ai |
