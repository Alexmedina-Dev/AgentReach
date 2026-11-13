# Historia 28: permiso en dos niveles

**Estado: terminada (2026-11-11).**

1. **Primera pregunta** (igual): «¿Se permite que AgentReach lea esta carpeta? (S/N)».
2. **Segunda pregunta**, aparte y en tercera persona: «AgentReach necesita ver las reglas de tus agentes en tu carpeta personal (solo las reglas, nunca los valores). Sin ellas no puede decidir bien los niveles. ¿Se permite? (S/N)» (formal: «sus agentes», «su carpeta»; inglés: «AgentReach needs to see the rules of your agents in your home folder... Is this allowed? (Y/N)»). Solo se hace si la primera fue S. Solo cuentan s, S, n y N (y, Y, n, N en inglés); lo demás se repite y tras tres intentos cuenta como N (se sigue sin leer fuera del proyecto).

## Con N no se abre ni se lista nada fuera del proyecto
- Configuración de usuario (`~/.claude/settings.json`, `~/.config/opencode`, el respaldo de `%APPDATA%` y `OPENCODE_CONFIG`) y los agentes del usuario.
- Configuración gestionada (y `managed-settings.d`).
- El `opencode.json` de las carpetas padre (ni siquiera se busca el `.git` hacia arriba).
- El archivo global de AgentReach `~/.agentreach/config.toml` (ahora se lee **después** de las dos preguntas, y solo con S).
- La detección de agentes del ámbito usuario, y los colectores de ubicaciones sensibles y de instrucciones fuera del proyecto (aunque esté el opt-in).
- Los niveles que dependen de las reglas quedan en «potencial» (reglas incompletas) y el reporte dice por qué: nuevo motivo `sin_permiso_fuera_del_proyecto` («No se leyeron las reglas de fuera del proyecto (no se dio permiso)», con cómo cambiarlo), que sale en la sección «Por qué hay niveles "no determinado"» (terminal, HTML y exportaciones) con los archivos que no se leyeron.

`Configuracion.lectura_fuera` (por defecto verdadero para uso como biblioteca; la línea de comandos lo pone en falso con N).

## Pruebas
`tests/test_historia_28.py` (21): textos en los tres idiomas/tonos, orden, respuestas, y una **vigilancia** (ganchos de auditoría de `open`, `os.listdir`, `os.scandir` y `glob`) que comprueba que con N no se abre ni se lista nada de la carpeta personal, la configuración gestionada ni el repositorio padre (con todas las opciones, incluido el opt-in), y que con S la misma vigilancia SÍ ve esos accesos (control). Verificada con mutaciones (quitar la condición de las carpetas padre o de la detección de usuario rompe las pruebas).

## No verificado
Linux/macOS (rutas gestionadas) y una terminal real de Windows.
