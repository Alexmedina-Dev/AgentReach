# Historia 27: letras de las preguntas y tope por nombre

**Estado: terminada (2026-11-11).**

## (1) Las preguntas
Muestran **(S/N)** en mayúsculas y, en inglés, **(Y/N)**. Cuentan solo las letras que se muestran: en español s, S, n y N; en inglés y, Y, n y N (una «s» no vale en inglés, ni una «y» en español). Enter solo, «si», «yes», espacios, etc. se vuelven a preguntar; tras tres intentos se sale sin leer (la pregunta de abrir el navegador: ni se abre ni se recuerda nada).

## (2) Una variable o clave reconocida solo por su nombre nunca pasa de «potencial»
Decisión de Alex (2026-11-11), en ningún agente, incluido opencode (PP-01a a PP-01f). AgentReach reconoce las credenciales por el NOMBRE de la variable (nunca ve el valor), así que `NIVEL_MAXIMO[TH-1]` pasó de comprobado a potencial (el motivo sale como «sin fuente verificada»; la regla, si la hay, sigue mandando: `regla_deny`, `regla_ask`...).

**Consecuencias (para que Alex las confirme):**
- Un proyecto cuyo único hallazgo es una credencial por nombre sale con **código 0** (antes 1): el código 1 queda para lo comprobado por el texto (git que ejecuta programas, texto invisible, instrucciones fuera del proyecto, remoto de git con credenciales).
- Oráculo (`tests/oraculo/expected.json`): PP-01 (opencode), PP-04, PP-05, GT-01, PA-01 y AJ-01 (Claude Code) pasan de comprobado a potencial, y PP-01a a PP-01f ya no tienen «diferencia aceptada». Cifras por agente: **13 comprobado, 33 potencial, 2 hipótesis** (antes 18/28/2). Cada caso cambiado lleva el campo `decision`.
- Las pruebas del motor de niveles (reglas, permisos, herencia, flujo) usaban TH-1 como ejemplo de «comprobado»: llevan la marca `sin_tope_por_nombre` (tests/conftest.py), que levanta el tope solo ahí. Las pruebas del tope real (`tests/test_historia_27.py`, el oráculo) no la llevan.

Pruebas: `tests/test_historia_27.py` (30).
