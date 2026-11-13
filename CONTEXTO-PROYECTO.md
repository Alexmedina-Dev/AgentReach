# AgentReach — Contexto del proyecto (para BMAD)

> Documento de arranque. Úsalo como insumo del product brief y del PRD.
> Autor: Alex · Fecha: 2026-11-05 · Idioma de trabajo: español

## 1. Idea en una frase

**AgentReach** es un analizador de exposición de agentes de IA (*Agent Environment & Capability Exposure Analyzer*): revisa un repositorio y su entorno de desarrollo para mostrar **qué podría alcanzar o ejecutar realmente un agente de IA**, aunque nadie se lo haya autorizado explícitamente.

## 2. Problema

Los agentes de IA (Claude Code, Cursor, etc.) suelen tener más capacidad de la que sus usuarios creen. Un desarrollador puede indicar "trabaja solo en `src/`", pero desde ahí el agente podría llegar de forma indirecta a:

- un `.env` con credenciales de producción,
- tokens de GitHub con permisos de escritura,
- credenciales de AWS u otras nubes (`~/.aws`, `~/.ssh`),
- scripts de deploy, migraciones o configuración de Terraform,
- instrucciones maliciosas escondidas en `README.md`, `CLAUDE.md` o `AGENTS.md` (prompt injection).

## 3. Diferenciador

Las herramientas existentes auditan sobre todo la **configuración declarada**: servidores MCP, reglas `allow` y secretos en configs (ver sección 9). AgentReach mide otra cosa:

> **La brecha entre los permisos declarados y las capacidades efectivas.**

| Permiso declarado | Capacidad encontrada | Riesgo |
|---|---|---|
| Leer `src/` | Acceso indirecto a `.env` | Crítico |
| Editar código | Script de deploy disponible | Alto |
| Leer documentación | Instrucciones sospechosas | Medio |
| Sin permisos de publicación | Credenciales de GitHub disponibles | Alto |

*(Ejemplo ilustrativo, no es un resultado de escaneo real.)*

## 4. Qué analiza (cuatro ejes)

1. **Credenciales:** secretos y tokens accesibles.
2. **Capacidades:** deploy, push, migraciones, scripts de alto impacto.
3. **Instrucciones:** archivos con instrucciones sospechosas para el agente.
4. **Alcanzabilidad:** relaciones entre los permisos declarados y los recursos.

## 5. Principio de rigor (requisito no negociable)

No se debe afirmar que un recurso es alcanzable solo porque existe una referencia a él. El modelo debe considerar permisos del sistema operativo, directorios montados, enlaces simbólicos, variables de entorno, comandos disponibles y límites del sandbox.

Cada hallazgo se clasifica con un nivel de confianza:

- **Acceso comprobado**
- **Acceso potencial**
- **Hipótesis**

No se promete calcular "todo lo que un agente podría hacer": el resultado depende del entorno, el sistema operativo, las credenciales, las herramientas y el contexto de ejecución.

## 6. Salidas esperadas

- Mapa de exposición.
- Hallazgos priorizados.
- Puntaje de riesgo: **Agent Exposure Score (AES)**.
- Recomendaciones de mitigación.
- Reporte en Markdown y SARIF.

### Agent Exposure Score (AES)

Se basa en: sensibilidad del recurso, alcanzabilidad, capacidad de escritura o ejecución, impacto potencial y diferencia entre autorización y capacidad efectiva. **No usar una suma arbitraria:** definir una metodología documentada y validarla con escenarios controlados.

## 7. Alcance por etapas

| Etapa | Funcionalidad | Prioridad |
|---|---|---|
| 1 | Escaneo de credenciales y archivos sensibles | MVP |
| 2 | Detección de scripts y acciones de alto impacto | MVP |
| 3 | Detección de instrucciones sospechosas | MVP |
| 4 | Análisis de alcanzabilidad entre recursos | Diferenciador |
| 5 | Evaluación de riesgo y scoring (AES) | Diferenciador |
| 6 | Integración con Claude Code, Cursor y MCP | Evolución |
| 7 | CI/CD y SARIF avanzado | Evolución |

**Fuera del MVP:** auditoría de identidades en la nube (AWS/GCP/Azure/K8s), monitoreo en tiempo de ejecución, y corrección automática de hallazgos.

## 8. Decisiones técnicas iniciales

- **Forma:** CLI, análisis estático y de solo lectura (no modifica el repo ni el entorno, no hace llamadas de red por defecto).
- **Lenguaje:** Python (inspección de archivos, permisos, análisis estático, reportes).
- **Entorno de ejecución:** el equipo no tiene Python instalado; BMAD requiere `uv` (`https://docs.astral.sh/uv/`), que también puede provisionar el intérprete.
- **Plataforma de trabajo:** Windows 11, por lo que el análisis de permisos debe contemplar rutas y ACL de Windows además de POSIX.
- **Privacidad:** los reportes no deben imprimir valores de secretos; solo la ubicación y el tipo.

## 9. Competencia a revisar antes del PRD

Para no repetir lo que ya existe, revisar (no verificado el estado de mantenimiento de ninguno):

- AgentSec (`agentsec-cli`, PyPI): analiza permisos de agentes de código, reglas de Cursor y configs MCP.
- Bulwark (`bulwark-scanner`, PyPI): reglas `allow` amplias, operaciones destructivas preaprobadas.
- mcp-audits y mcp-audit-scanner (PyPI): auditoría de servidores MCP.
- agent-audit-kit: escáner para 13 plataformas de agentes.
- nhi-audit y Agentcheck: identidades y credenciales en la nube.
- Referencia de cobertura: OWASP Top 10 for Agentic Applications (2026).

## 10. Usuarios objetivo

Desarrolladores que usan agentes de IA, equipos DevSecOps y equipos de seguridad de IA.

## 11. Preguntas abiertas para el PRD

1. ¿Cómo se representa lo "declarado"? (config de Claude Code, `AGENTS.md`, reglas de Cursor, o un archivo propio de política).
2. ¿Qué evidencia basta para marcar "acceso comprobado" frente a "potencial"?
3. ¿Cómo se valida el AES? (repos de prueba con exposición conocida).
4. ¿Cómo se manejan los falsos positivos y los secretos de ejemplo?
5. ¿Se escanea solo el repo o también el home del usuario (`~/.aws`, `~/.ssh`)? Implicaciones de privacidad.

## 12. Criterios de éxito (borrador)

- Detecta al menos un caso de brecha declarado-vs-efectivo que las herramientas de la sección 9 no reportan.
- Cero valores de secretos en los reportes.
- Cada hallazgo incluye ruta, nivel de confianza y mitigación sugerida.
- Se ejecuta sobre un repo mediano en tiempo razonable y sin red.

## 13. Cómo arrancar con BMAD

1. Abrir Claude Code dentro de esta carpeta.
2. Invocar `bmad-help` para ver el flujo recomendado.
3. Pedir al Analyst el *product brief* usando este archivo como insumo; luego PRD con el PM, arquitectura y historias.
