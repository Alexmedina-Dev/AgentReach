---
title: "AgentReach — Product Brief"
status: draft
created: 2026-11-05
updated: 2026-11-05
---

# AgentReach — Product Brief

## Visión

AgentReach te muestra a qué puede acceder un agente de IA en tu entorno, con evidencias y niveles de confianza.

AgentReach es una herramienta de código abierto y agnóstica al fabricante. En el MVP audita y advierte. La visión a largo plazo es una capa de seguridad, control y observabilidad para agentes de IA: que además controle lo que pueden hacer y registre lo que realmente hicieron. Esas capacidades llegan en fases posteriores, por plataforma y solo donde el agente lo permita.

## Problema

Los agentes de IA actúan con los permisos de quien los ejecuta. Una instrucción como "trabaja solo en `src/`" no limita lo que el agente puede tocar: desde ahí puede llegar a credenciales, claves SSH, tokens, scripts de deploy o instrucciones maliciosas en archivos de contexto (`README.md`, `CLAUDE.md`, `AGENTS.md`).

El problema se ve en las noticias: agentes que rompen ciclos sin que se les pida, borran archivos sin avisar o ejecutan acciones fuera de la tarea. Muchas de esas acciones están permitidas por los permisos que el agente ya tenía. Por eso la primera pregunta es: **qué le permite el entorno que haga.**

## Diferenciador

Las herramientas de comunidad existentes (AgentSec, Bulwark, mcp-audits y otras) revisan sobre todo la **configuración declarada**: reglas `allow`, servidores MCP, secretos en archivos de config.

AgentReach mide la **brecha entre lo declarado y lo efectivamente alcanzable**: lo que el agente puede tocar, considerando permisos del sistema operativo, directorios montados, enlaces simbólicos, variables de entorno y herramientas disponibles.

*Por verificar: que ninguna herramienta existente mida esa brecha de forma equivalente.*

## Alcance del MVP

**Incluye:**
1. Auditoría estática del entorno: archivos, repositorios, variables de entorno, credenciales, claves SSH, tokens, scripts, procesos y accesos de red alcanzables.
2. Identificación de permisos, accesos y riesgos.
3. Informes con evidencias y niveles de confianza: **comprobado**, **potencial** e **hipótesis**.
4. Arquitectura modular para incorporar nuevos agentes.
5. Un adaptador de referencia: Claude Code.

**No incluye:** bloquear acciones, prevención en tiempo de ejecución, monitoreo en vivo, ni auditoría de identidades en la nube.

**Regla de honestidad:** el MVP **audita y advierte**. No promete prevención. Esa capacidad llegará después, por plataforma, y solo donde la plataforma la permita.

## Arquitectura

- **Núcleo agnóstico:** analiza el entorno real de ejecución y produce hallazgos con un formato común. No depende de Claude Code, Cursor, Codex ni de ninguna marca.
- **Adaptadores por plataforma:** cada uno interpreta las configuraciones de su agente y declara qué capacidades reales ofrece: solo auditar, auditar y advertir, o auditar y bloquear.
- **Instalación:** global (disponible en todos los proyectos, con preferencias generales) y por proyecto (reglas y política propias del repositorio, compartibles con el equipo).
- **Diseño preparado para fases posteriores:** la capa de prevención y la de observabilidad deben poder añadirse sin reescribir el núcleo.

## Principios

1. **Open source y confianza:** cualquiera puede inspeccionar cómo funciona.
2. **Seguridad por diseño:** solo lectura en la auditoría, sin red por defecto, sin enviar información privada a servidores externos.
3. **Independencia de plataformas:** no pertenece a un único agente ni a una única empresa.

## Fases

| Fase | Alcance | Naturaleza |
|---|---|---|
| 1 — MVP | Conocer y advertir sobre la exposición; adaptador Claude Code | Estática |
| 2 — Observabilidad | Registrar acciones, detectar operaciones fuera de alcance, historial auditable | Posterior / en ejecución |
| 3 — Protección | Políticas configurables, aprobaciones, bloqueos donde la plataforma lo permita | En ejecución |

## Usuarios

- **Principal:** desarrolladores que usan agentes de IA en sus propios repositorios.
- **Secundario:** equipos de desarrollo y DevSecOps que quieren compartir políticas.
- **Largo plazo:** empresas.

## Criterios de éxito (borrador)

- Detecta al menos un caso de brecha entre lo declarado y lo alcanzable que las herramientas existentes no reportan.
- Cero valores de secretos en los reportes.
- Cada hallazgo incluye ruta, nivel de confianza y mitigación sugerida.
- Se ejecuta sin red y sin modificar el repositorio.
- Un tercero puede añadir un adaptador nuevo siguiendo la documentación, sin tocar el núcleo.

## Preguntas abiertas

1. **Adaptadores:** ¿qué agentes usan las personas que lo probarán? Define el segundo adaptador.
2. **Representación de lo declarado:** ¿config de Claude Code, `AGENTS.md`, reglas de Cursor o un archivo de política propio?
3. **Evidencia:** ¿qué basta para pasar de "potencial" a "comprobado"?
4. **Validación del puntaje AES:** ¿con qué repositorios de prueba de exposición conocida?
5. **Falsos positivos y secretos de ejemplo:** ¿cómo se tratan?
6. **Alcance del escaneo:** ¿solo el repo o también el home del usuario (`~/.aws`, `~/.ssh`)? Implicaciones de privacidad.
7. **Verificación de plataforma:** confirmar qué puntos de control ofrece cada agente antes de prometer algo por adaptador.
