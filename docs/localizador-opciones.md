# Localizador de líneas: biblioteca estándar frente a librerías externas

## El problema

Cada hallazgo de AgentReach debe decir en qué archivo y en qué línea está. Los lectores que trae
Python (`json` para JSON y `tomllib` para TOML) devuelven los datos pero **no** el número de línea.
Además, AgentReach nunca debe imprimir valores de secretos, así que lo que se necesita es solo una
posición: la línea de una clave, de un elemento de un arreglo o de una variable de un `.env`.

## Qué se implementó (solo biblioteca estándar)

Módulo `src/agentreach/infra/localizador.py`, con pruebas en `tests/test_localizador.py`.

- `localizar_clave(texto, formato, ruta_clave)` devuelve la línea (desde 1) o `None`.
- `localizar_posicion(...)` devuelve `(línea, columna)`.
- Formatos: JSON, JSON con comentarios (llamado JSONC), TOML y `.env`.
- Recibe el texto ya leído; no abre archivos ni guarda valores. De cada archivo solo retiene nombres
  de claves y números.
- Ante cualquier duda devuelve `None` (texto mal formado, clave repetida, ruta que cae dentro de una
  tabla o arreglo "en línea" de TOML). Nunca adivina.
- Resultado de las pruebas: 32 pasan y 3 se omiten (las 3 son de reglas no negociables que ya
  estaban marcadas como pendientes; no son del localizador). Comando: `uv run pytest`.
- Costo: unas 530 líneas, cero dependencias nuevas.

Límite conocido: en TOML no localiza claves dentro de tablas en línea (`a = {b = 1}`) ni dentro de
arreglos en línea (`a = [1, 2]`); devuelve `None`. En archivos de configuración de agentes esto es raro.

## Alternativas externas probadas

Probadas en un entorno temporal fuera del repositorio con `uv run --no-project --with ...`
(Python 3.13.17; el proyecto exige 3.12 o superior, no se probó en 3.12 exacto). Los tamaños son la
suma de archivos instalados, medida por `importlib.metadata`.

| Librería | Versión probada | Qué hace | ¿Da líneas? | Peso instalado |
|---|---|---|---|---|
| `tomlkit` | 0.15.2 | Lee y reescribe TOML conservando comentarios y formato | **No**. Verificado: los elementos no exponen línea (solo `trivia` con espacios y comentarios) | unos 209 KB, 19 archivos, sin dependencias |
| `ruamel.yaml` | 0.19.1 | Lee YAML conservando comentarios | **Sí**, en YAML: `doc.lc.data` da línea y columna (verificado). Pero YAML no es un formato de la lista actual | unos 546 KB, 41 archivos; dependencias opcionales (`clib`) |
| `json5` | 0.17.3 | Lee JSON con comentarios y comas finales | **No**. Verificado: `json5.parse` devuelve `(datos, error, posición_final)`; solo los errores traen columna | unos 168 KB, sin dependencias |
| `pyjson5` | 2.0.1 | Lo mismo, en C/Cython (rápido) | **No**. Verificado: solo mensajes de error con posición | unos 338 KB; es extensión compilada, requiere una rueda (wheel) por plataforma |

Lo no verificado: no se probó si existen forks o complementos de estas librerías que añadan líneas, ni
el comportamiento de cada una en Python 3.12 exacto, ni sus historiales de seguridad.

## Lectura en lenguaje llano

- Ninguna de las librerías de JSON o TOML probadas resuelve el problema por sí sola: leen los datos
  y los entregan sin decir de qué línea salieron. Habría que escribir igualmente un buscador por
  encima, y entonces la dependencia no ahorra el trabajo principal.
- La única que da posiciones es `ruamel.yaml`, pero para YAML, un formato que hoy no está en alcance.
  Si más adelante se admiten agentes con configuración en YAML, es el candidato natural.
- Las librerías que **leen valores** (todas las anteriores) los cargan en memoria. Para una
  herramienta que promete no tocar secretos, un escáner propio que salta los valores sin copiarlos es
  más fácil de auditar y de demostrar con la prueba canario.

## Riesgo de añadir dependencias a una herramienta de seguridad

- Cada dependencia amplía la superficie de ataque de la cadena de suministro: una versión
  comprometida corre con los permisos de AgentReach, que lee configuraciones sensibles.
- Contradice la decisión vigente del proyecto (solo biblioteca estándar) y complica el empaquetado
  con `uv_build`, sobre todo con extensiones compiladas como `pyjson5`.
- Hay que vigilar actualizaciones y avisos de seguridad de cada paquete adicional.

## Recomendación

1. **Mantener el localizador estándar.** Resuelve los tres formatos del alcance, sin dependencias, y
   es lo único que garantiza no copiar valores.
2. Seguir usando `json` y `tomllib` del estándar para leer los datos, y el localizador solo para la
   línea. La consistencia entre ambos se protege con pruebas (si el escáner no puede confirmar la
   clave, devuelve `None` y el hallazgo se informa sin línea, nunca con una línea inventada).
3. Revisar `ruamel.yaml` solo si el alcance incorpora YAML. Hasta entonces, no añadir dependencias.
4. Si aparecen casos reales de TOML en línea que importen, ampliar el escáner propio antes de
   considerar una librería.
