# Historia 26: GitHub Copilot, un solo agente cuando la única señal es compartida

**Estado: terminada (2026-11-10).**

`.github/copilot-instructions.md` (y `.github/instructions/**.instructions.md`) los leen a la vez Copilot en VS Code y su línea de comandos. El catálogo los listaba como firma fuerte de los dos agentes, así que salían dos, y eso afirmaba una superficie concreta por una señal compartida (regla del catálogo).

- Si lo único de Copilot es esa señal: se reconoce **un** agente, «GitHub Copilot (VS Code o su línea de comandos)» (id `github-copilot`, confianza alta: Copilot está configurado; no se dice en qué superficie), sin análisis de alcance todavía.
- Si una sola superficie tiene señales propias (VS Code: `.github/agents/*.agent.md`, prompts; CLI: `~/.copilot/...`): queda esa, y la otra, que solo tenía la compartida, se descarta.
- Si las dos tienen señales propias: quedan las dos.
- Los demás agentes no cambian. La lógica está en `app/agentes.py` (`_unificar_copilot`).

Pruebas: `tests/test_historia_24.py` (7 nuevas, 58 en total), incluida la salida del JSON del HTML y de la terminal (un solo Copilot).

Pendiente: el nombre unificado va solo en español (el campo `name` no es bilingüe); en inglés el nombre sale igual.
