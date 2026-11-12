# Diseño del reporte de terminal de AgentReach (MVP)

Fecha: 2026-11-09. Es una propuesta de diseño: no cambia código, pruebas ni historias. El reporte en HTML es de la fase 2; este documento solo cubre lo que se imprime en la terminal de Windows (PowerShell).

Qué reemplaza: el reporte mínimo de la Historia 5b (`reporting/texto_minimo.py`), que imprime una línea por hallazgo con la ruta absoluta, el código `TH-1`, "potencial (provisional)" y los identificadores `archivo_ilegible` o `ubicacion_sensible_sin_activar`. Lo que Alex vio mal: líneas partidas a mitad de palabra, rutas enormes, códigos sin explicar, todo plano.

Las cuatro muestras están en `docs/reporte-terminal/muestras/` (ver sección 10). Se generaron con un prototipo de maqueta (no es código del producto), con los datos del proyecto de prueba y sin ningún valor con forma de secreto.

## 0. Decisiones que son de Alex (elección de producto)

Todo lo demás de este documento es propuesta técnica. Estas ocho son elecciones de producto y están marcadas en el texto como **decisión pendiente de Alex**.

| # | Decisión | Lo que propongo |
|---|---|---|
| P1 | ¿Una sola sección "Qué no pudo revisar AgentReach" con dos partes (A: esta carpeta, B: límites fijos), o dos secciones separadas? | Una sola, con las dos partes (así nadie lee "no se pudo revisar" sin ver los límites). |
| P2 | Idioma cuando la configuración regional no dice español ni inglés (o no se puede leer). | Español, porque es el idioma de la persona que usa el proyecto hoy. |
| P3 | Tratamiento: "usted" (lo que usa el catálogo de explicaciones de `finding.py`) o "tú" (lo que usa el boceto HTML). | "Usted" en la terminal, por coherencia con el catálogo ya escrito. |
| P4 | Caracteres peligrosos en un nombre: borrarlos en silencio (como hace hoy `limpiar_ruta`) o mostrarlos escritos (`\u202e`). | Mostrarlos escritos y avisar con una nota. Borrar en silencio disfraza el nombre real. |
| P5 | Código de salida: ¿un `3` para "error interno"? ¿Debe "no se pudo revisar" cambiar el código? | `3` para error interno. "No se pudo revisar" no cambia el código (0 o 1 como en la Historia 13), pero se ofrece `--estricto` más adelante. |
| P6 | ¿Pintar el fondo de la terminal con `#0B1114` (fondo de la marca)? ¿Qué hacer en terminales de fondo claro? | No pintar fondo (se respeta el tema de la persona). Usar la variante oscura de la paleta de `colores.md` solo si la terminal avisa fondo claro. |
| P7 | En un mismo archivo, si dos hallazgos son del mismo tipo, ¿repetir "qué hacer / qué significa" o decir "igual que el de la línea N"? | Decir "igual que el de la línea N" en la versión compacta y repetir todo con `--detalle`. |
| P8 | ¿Se agrega `--salida ARCHIVO` (AgentReach escribe el archivo él mismo en UTF-8) para no depender de `>` de PowerShell? | Sí, y recomendarlo en la ayuda. Ver sección 4. |

Detalles menores que también elegí yo y se pueden cambiar sin dolor: ancho máximo 100 columnas, rutas relativas siempre con `/`, el nombre de los interruptores (`--detalle`, `--idioma`, `--color`, `--ascii`, `--ancho`), que son [SUPUESTO] como en la Historia 5b.

## 1. Estructura del reporte

De arriba abajo, siempre en este orden:

1. **Encabezado.** Marca (AGENT en blanco, REACH en menta), título, **carpeta revisada con su ruta absoluta** (es el único lugar donde sale completa), fecha y hora local, y la frase "Solo lectura: no cambió nada ni ejecutó ningún programa".
2. **Aviso de secretos** (azul, con "(i)"): "No se muestran valores de secretos. AgentReach nunca copia contraseñas, tokens ni claves: solo dice dónde están y de qué tipo son." Sale en todo reporte, también en uno vacío.
3. **Resumen**, arriba de todo lo demás: cuántos archivos se miraron y un conteo por nivel (comprobado, potencial, hipótesis) más "no se pudo revisar", cada uno con su símbolo, su palabra y una descripción corta.
4. **Hallazgos**, agrupados primero por nivel (comprobado, potencial, hipótesis; el orden de la Historia 13) y dentro de cada nivel por archivo (ruta relativa sola en su línea, en negrita), y dentro del archivo por línea. El grupo de hipótesis lleva el rótulo "Sugerencias, no accesos comprobados" (lo exige la Historia 13, prueba m).
5. **Qué no pudo revisar AgentReach** (sección fija, sale siempre):
   - **A. En esta carpeta:** entradas concretas, agrupadas por motivo. Cada motivo trae su nombre legible, las rutas y "Cómo resolverlo" una sola vez.
   - **B. Límites de la herramienta:** los seis límites de FR-21 y la línea de "tampoco se revisan en esta versión" (historial de commits de git, cambios después de aprobar una configuración, procesos y puertos). Texto fijo, en el idioma elegido.
6. **Cierre:** código de salida en palabras y la pista de `--detalle`.

Si no hay hallazgos, en lugar de la sección 4 sale "√ SIN HALLAZGOS" con la frase "Eso no significa que el agente no pueda hacer daño: lea qué no se pudo revisar", y las secciones A y B salen igual (FR-20 y FR-21). (Ese caso no tiene muestra propia; el prototipo lo genera igual que las demás.)

### 1.1 Los ocho campos en la versión compacta

Cada hallazgo es un bloque de cuatro a seis líneas. Las etiquetas son las de `docs/vocabulario-es-en.md`.

| Campo | Dónde sale en la versión compacta |
|---|---|
| 1 Ubicación | Archivo como título del grupo y, en la primera línea del hallazgo, "línea 2" (o "línea no determinada"). |
| 2 Qué es y de quién | Primera línea: nombre legible del tipo y, entre paréntesis, el proveedor ("servicio de pagos"). |
| 3 Nivel y por qué | Línea "Nivel y por qué:" con el nivel y la razón fija del catálogo. |
| 4 Ajeno a la tarea | En la línea de plataforma: "Ajeno a la tarea: sí / no / no determinado". |
| 5 Plataforma y agente | Línea "Plataforma y agente:". |
| 6 Postura del agente | En la misma línea: "Reglas del agente: sin regla / pide confirmación / lo bloquea (solo por regla)". |
| 7 Qué hacer | Línea con flecha (menta). |
| 8 Qué significa | Línea siguiente. |

Con **`--detalle`** cada campo va en su propia línea y se agregan los datos técnicos que en la versión compacta no salen: la ubicación exacta (`.env:2`), el **código del catálogo** (`TH-1`), el **motivo técnico** (`existe_legible_sin_regla`), el archivo y la línea de la regla que fija la postura, y "Fuente verificada: sí/no". Es el único lugar donde aparecen códigos e identificadores. Ejemplo real generado (primer hallazgo de las muestras):

```text
.env.local
  ■ línea 2 · Credencial en un archivo (servicio de inteligencia artificial)
    Ubicación: .env.local:2
    Código del catálogo: TH-1
    Nivel y por qué: comprobado. Existe, el sistema operativo permite leerlo y
      ninguna regla del agente lo impide.
    Motivo técnico: existe_legible_sin_regla
    Plataforma y agente: Claude Code
    Reglas del agente: sin regla
    Ajeno a la tarea: no determinado
    Fuente verificada: no
    → Qué hacer: Saque la credencial del proyecto o guárdela en un gestor de
      secretos, y rote la clave si estuvo expuesta.
    Qué significa: Un archivo del proyecto guarda una credencial (una clave o
      contraseña que da acceso a un servicio). Un agente que pueda leer el
      proyecto podría leerla.
```

### 1.2 "Qué no pudo revisar", por motivo

Se agrupan por motivo para no repetir el mismo "cómo resolverlo" diez veces. Los nombres de los motivos están en la sección 5.2. Las rutas fuera de la carpeta revisada (las tres ubicaciones sensibles) salen con `~` para "su carpeta personal", y el reporte lo explica en la introducción de la parte A. `ubicacion_sensible_sin_activar` nunca se escribe como "revisado" ni como "sin hallazgos" (Historia 13, prueba k).

## 2. Legibilidad: ancho, rutas y sangría

- **Ancho real.** `shutil.get_terminal_size(fallback=(80, 24)).columns`. Si la salida no es una terminal, se usa 80 (o la variable `COLUMNS` si existe; `get_terminal_size` ya la mira primero).
- **Ancho de trabajo `W = clamp(columnas, 60, 100)`.** Mínimo 60 porque por debajo no hay forma de que quepan las etiquetas. Máximo 100 porque las líneas de más de 100 letras cansan (elección mía, se puede cambiar).
- **Se escribe hasta `W - 1`.** La consola antigua de Windows salta de línea cuando se llena la última columna y deja una línea en blanco de más; con una columna de margen no pasa.
- **Ajuste en límites de palabra con sangría francesa:** la primera línea de un campo empieza en la sangría del campo y las siguientes 2 espacios más adentro (se ve en las muestras). No se corta ninguna palabra, tampoco después de un guion (`--incluir-ubicaciones-sensibles` entero).
- **Nunca se corta una ruta.** Una ruta es una "ficha indivisible": va sola en su línea (título del grupo, lista de no revisados) o, si va dentro de una frase, se trata como una sola palabra aunque lleve espacios. Si una ruta es más larga que el ancho, se deja entera y la terminal la parte sola (es la única excepción posible; no se inserta ningún salto ni se abrevia con "..."). Con ancho 60, la ruta absoluta del encabezado pasa sola a su propia línea (se ve en `muestra-3-es-ancho-60.txt`).
- **Rutas relativas a la carpeta revisada**, con `/` como separador siempre, para que el texto sea igual en cualquier equipo. `.env:2` se puede seleccionar y abrir con Ctrl+clic en terminales que lo permiten. La ruta absoluta sale solo en el encabezado. Lo que está fuera de la carpeta (las ubicaciones sensibles del usuario, el destino de un enlace) sale con `~` si está en la carpeta personal y absoluta si no.
- **Medir con el ancho que se ve, no con `len()`.** `textwrap` cuenta caracteres; un nombre con letras chinas o emoji ocupa dos columnas y descuadraría el ajuste. Se mide con una función de unas 8 líneas que suma 2 a los caracteres de ancho doble (`unicodedata.east_asian_width` en `W` o `F`) y 0 a los que se pegan al anterior. El ajuste en sí es un recorrido palabra por palabra (también unas 20 líneas, ver el prototipo).
- **El color se pone después de ajustar.** Primero se mide y se parte el texto plano; después se pinta cada línea. Si se pintara antes, los códigos de color contarían como letras y las líneas saldrían cortas.
- **Si la terminal es más angosta que 60**, el diseño sigue usando 60 y la terminal parte las líneas; no se intenta nada más.

## 3. Color

Paleta A de `docs/boceto-reporte/colores.md`. El color **nunca es lo único**: cada nivel lleva siempre símbolo y palabra.

| Rol | Palabra (ES / EN) | Símbolo (Unicode / respaldo) | 24 bits (fondo oscuro) | 16 colores | Variante fondo claro |
|---|---|---|---|---|---|
| Comprobado | COMPROBADO / VERIFIED | ■ / `[!!]` | rojo `#FF6B6B` | rojo brillante (91) | `#B3201A` |
| Potencial | POTENCIAL / POTENTIAL | ▲ / `[!]` | ámbar `#FFB224` | amarillo (33) | `#7A4300` |
| Hipótesis | HIPÓTESIS / HYPOTHESIS | ◊ / `[?]` | gris `#A9BDB9` | blanco (37) | `#3A524D` |
| No se pudo revisar | NO SE PUDO REVISAR / COULD NOT CHECK | ○ / `[-]` | violeta `#B9A2FF` | magenta brillante (95) | `#5A3DC0` |
| Sin hallazgos y acciones ("Qué hacer", "Cómo resolverlo", REACH) | SIN HALLAZGOS / NO FINDINGS | √ / `[ok]` y `→` / `->` | menta `#3DF5D0` | cian brillante (96) | `#005F4D` |
| Información (aviso de secretos, "solo lectura") | | `(i)` | azul `#6DB6FF` | azul brillante (94) | `#0A58A8` |
| Texto secundario (etiquetas, descripciones) | | | `#7C928E` | gris oscuro (90) | `#46635E` |

- Los colores de 24 bits (16 millones de colores) se escriben como secuencias ANSI: pequeños códigos de texto que la terminal entiende para pintar, con la forma `ESC[38;2;R;G;Bm`. Los de 16 usan los códigos clásicos `ESC[9Xm`. Cada trozo pintado termina con el código de "volver a normal" (`ESC[0m`), así un corte de línea, un `Ctrl+C` o un `| more` nunca dejan la terminal teñida.
- **Los símbolos elegidos** (■ ▲ ◊ ○ √ →) están en el juego de caracteres básico de Windows (el que traen Consolas y Cascadia). No usé el octágono, el rombo con "?" ni el círculo tachado del boceto HTML porque no existen como caracteres comunes; la forma distinta (cuadrado, triángulo, rombo, círculo) cumple el mismo papel para quien no distingue colores. Los símbolos son un refuerzo: lo que manda es la **palabra** en mayúsculas.
- **Cuándo se usa color** (de mayor a menor prioridad):
  1. `--color nunca` → sin color; `--color siempre` → con color aunque la salida no sea una terminal (para quien quiere guardar el texto con colores).
  2. Variable de entorno `NO_COLOR` con cualquier valor que no esté vacío → sin color (convención publicada en no-color.org).
  3. La salida no es una terminal (redirección a archivo, tubería) → sin color.
  4. `TERM=dumb` → sin color.
  5. En Windows hay que **activar** el modo de secuencias de la consola (`SetConsoleMode` con `ENABLE_VIRTUAL_TERMINAL_PROCESSING`, llamado con `ctypes`). Si falla, sin color.
  6. 24 bits solo si hay señal explícita: `COLORTERM` vale `truecolor` o `24bit`, o existe `WT_SESSION` (Windows Terminal), o `TERM_PROGRAM=vscode`. Si no hay señal, 16 colores. **No verificado:** si la consola clásica de Windows 11 acepta 24 bits sin señal; por eso el valor por defecto prudente son 16 colores.
- **No se pinta el fondo** (decisión pendiente de Alex, P6). La paleta está pensada para fondo oscuro; en fondo claro el ámbar `#FFB224` tiene muy poco contraste. Propuesta: leer `COLORFGBG` (la usan algunas terminales para decir si el fondo es claro u oscuro; Windows Terminal no la define) y, si dice claro, usar la columna "fondo claro" de la tabla. Interruptor opcional `--fondo claro|oscuro|auto`.
- **Solo se emiten secuencias de color** (las que terminan en `m`). Nunca movimiento del cursor, borrar pantalla, títulos de ventana ni enlaces: lo único que AgentReach imprime son colores propios, y todo lo demás pasa por la limpieza de la sección 7.

## 4. Codificación: cómo evitar texto roto en Windows

El problema: la misma salida se ve bien en la consola y se rompe ("Ã³" en lugar de "ó", o "?") al redirigir a un archivo o a otro programa, porque ahí Python usa la página de códigos regional (por ejemplo cp1252) y quien lee puede esperar otra cosa.

Reglas propuestas:

1. **El reporte se arma entero como texto y se escribe de una sola vez al final.** Así un error a mitad no deja medio reporte con un resumen engañoso, y la salida es estable.
2. **Si la salida es una terminal:** Python ya escribe a la consola con la interfaz Unicode de Windows (`sys.stdout.encoding` suele dar `utf-8`), así que no se cambia nada. Se comprueba que el texto se pueda codificar (`texto.encode(flujo.encoding)`); si no se puede (terminal rara), se usan símbolos ASCII (solo letras sin tildes y signos básicos) y las tildes se quitan con una transliteración (`unicodedata.normalize("NFKD", ...)` y descartar las marcas).
3. **Si la salida NO es una terminal (redirección o tubería):** reconfigurar con seguridad a UTF-8 y **símbolos ASCII de respaldo** (`[!!]`, `[!]`, `[?]`, `[-]`, `->`). Así lo único que podría romperse son las tildes, y no los símbolos.
   ```python
   def preparar_salida(flujo):
       try:
           flujo.reconfigure(encoding="utf-8", errors="replace")
       except (AttributeError, ValueError, OSError):
           pass  # StringIO de una prueba, flujo ya usado o cerrado: se sigue con lo que haya
   ```
   - `reconfigure` solo existe en los flujos reales de texto; una prueba que captura la salida con un `StringIO` no lo tiene, de ahí el `AttributeError`.
   - Se llama **solo dentro de `main()`**, nunca al importar el módulo, y una sola vez, antes de escribir.
   - `errors="replace"` garantiza que nunca salga un `UnicodeEncodeError` con traza: un carácter imposible se imprime como `?`.
   - **No** se usa `chcp`, `SetConsoleOutputCP` ni `PYTHONIOENCODING` desde dentro del programa: cambian la consola de la persona o de otros programas y se quedan así al terminar.
   - El mismo tratamiento se aplica a la salida de errores.
4. **`--ascii`** (y la variable `AGENTREACH_ASCII=1`) fuerzan símbolos ASCII **y** sin tildes, para quien alimenta una consola muy antigua.
5. **Escribir a un archivo:** en Windows PowerShell 5.1, `>` y `Out-File` pueden volver a codificar el texto (a UTF-16 o a la página de códigos de la consola, según el caso; es comportamiento conocido de esa versión y no lo comprobé en la máquina de Alex). Por eso propongo **`--salida ARCHIVO`** (decisión pendiente de Alex, P8): AgentReach escribe el archivo él mismo en UTF-8, sin color y sin depender de la redirección. La Historia 13 ya exige que rechace escribir dentro del proyecto auditado; esa opción lo necesita de todos modos.
6. **Nombres con caracteres que no son válidos en UTF-8** (Windows permite nombres con mitades de pares sustitutos): se muestran escritos (`\udc80`) antes de imprimir; si no, `print` fallaría. Entra en la limpieza de la sección 7.

## 5. Idioma y nombres legibles

### 5.1 Cómo se elige el idioma

Orden: `--idioma es|en|auto` → variable `AGENTREACH_IDIOMA` → configuración regional.

- **Windows:** `GetUserDefaultLocaleName` (con `ctypes`) devuelve algo como `es-CO` o `en-US`; se toman las dos primeras letras.
- **Otros sistemas:** variables `LC_ALL`, `LC_MESSAGES` y `LANG` (`es_CO.UTF-8`), en ese orden.
- `es*` da español; `en*` da inglés; cualquier otra cosa o fallo da español (**decisión pendiente de Alex, P2**).
- El nombre de los interruptores **no se traduce** (`--detalle` en los dos idiomas, y así lo dice el texto en inglés); los códigos de salida y los números tampoco.
- La fecha va en formato ISO (`2026-11-09 16:40`), igual en ambos idiomas, para que no se confunda día con mes.
- La palabra de inglés para "comprobado" es **VERIFIED**, no "confirmed" (regla de `docs/vocabulario-es-en.md`).

### 5.2 Nombres legibles de los tipos de hallazgo (20)

En pantalla solo sale el nombre. El código `TH-n` solo se ve con `--detalle`. Las explicaciones largas ("qué significa" y "qué hacer") ya existen en `CATALOGO_EXPLICACIONES`; esta tabla agrega el **título corto** que hoy no existe.

| Código (solo `--detalle`) | Español | English |
|---|---|---|
| TH-1 | Credencial en un archivo | Credential in a file |
| TH-2 | Llave privada para entrar a servidores | Private key to log in to servers |
| TH-3 | Credenciales de una cuenta en la nube | Cloud account credentials |
| TH-4 | Variable de entorno con nombre de credencial | Environment variable named like a credential |
| TH-5 | Archivo de instrucciones con texto sospechoso | Instructions file with suspicious text |
| TH-6 | Enlace que sale de la carpeta | Link that leaves the folder |
| TH-7 | Regla del agente demasiado permisiva | Agent rule that is too permissive |
| TH-8 | El agente puede ejecutar programas del equipo | The agent can run programs on the computer |
| TH-9 | Script de despliegue (publica cambios) | Deployment script (publishes changes) |
| TH-10 | Sin caja de aislamiento (sandbox) | No isolation box (sandbox) |
| TH-11 | Definición de agente | Agent definition |
| TH-12 | Texto invisible en un archivo de instrucciones | Invisible text in an instructions file |
| TH-13 | Archivo de instrucciones fuera de un proyecto | Instructions file outside a project |
| TH-14 | Programa que arranca solo con la configuración del proyecto | Program that starts by itself from the project settings |
| TH-15 | Configuración que salta las confirmaciones de permiso | Setting that skips permission checks |
| TH-16 | Tarea que arranca al abrir la carpeta | Task that starts when the folder is opened |
| TH-17 | Secreto de plataforma o de despliegue | Platform or deployment secret |
| TH-18 | Git configurado para ejecutar programas | Git set up to run programs |
| TH-19 | Dirección de git con credencial o sospechosa | Git address with a credential, or suspicious |
| TH-20 | Configuración de git que AgentReach no pudo leer | Git configuration AgentReach could not read |

TH-21 y TH-22 (memoria y conversaciones de agentes) existen en el PRD pero no en la enumeración `Tipo` de 20 miembros; cuando entren al código necesitarán su fila aquí, con el tono neutro que pide el PRD ("ubicación sensible y capacidad añadida").

### 5.3 Nombres legibles de los motivos de "no se pudo revisar" (10) y su "cómo resolverlo"

Un texto por motivo, en los dos idiomas (prueba de cobertura de la Historia 13, k). El identificador solo sale con `--detalle`. Los textos en inglés están en el prototipo; aquí van los de español.

| Identificador (solo `--detalle`) | Nombre en pantalla | Cómo resolverlo |
|---|---|---|
| `ubicacion_sensible_sin_activar` | Ubicación sensible sin activar | Si quiere que AgentReach mire solo el nombre, el tamaño y los permisos (nunca el contenido) de estas carpetas, ejecute de nuevo con `--incluir-ubicaciones-sensibles`. |
| `archivo_ilegible` | No se pudo abrir el archivo | Compruebe que el archivo existe y que su usuario tiene permiso de lectura; luego ejecute de nuevo. |
| `archivo_demasiado_grande` | Archivo demasiado grande (más de 5 MB) | Por seguridad AgentReach no abre archivos tan grandes. Si puede guardar secretos, revíselo a mano. |
| `no_es_archivo_regular` | No es un archivo normal (tubería, dispositivo u otro) | No requiere acción. Si no debería estar en el proyecto, retírelo. |
| `codificacion_no_utf8` | Texto en una codificación que no se pudo leer | Guárdelo como UTF-8 (un formato de texto estándar) y ejecute de nuevo. |
| `profundidad_excedida` | Demasiados niveles de anidación | Simplifique el archivo o revíselo a mano. |
| `ruta_de_red` | Ruta de red | AgentReach no sale a la red. Copie la carpeta al equipo y ejecute de nuevo. |
| `configuracion_no_interpretable` | Configuración que AgentReach no entiende | Revise ese archivo a mano. |
| `version_no_reconocida` | Versión de la herramienta no reconocida | Revise esa configuración a mano. |
| `historial_git_fase2` | Historial de git (llega en una fase futura) | Esta versión no ejecuta git. Si le preocupa el historial, revíselo con una herramienta aparte. |

### 5.4 Otras tablas de nombres

| Dato | Valor interno | Español | English |
|---|---|---|---|
| Proveedor | `ia` | servicio de inteligencia artificial | AI service |
| | `pagos` | servicio de pagos | payments service |
| | `codigo` | servicio de alojamiento de código | code hosting service |
| | `despliegue` | plataforma de despliegue | deployment platform |
| | `base_de_datos` | base de datos | database |
| | `nube` | cuenta en la nube | cloud account |
| | `ssh` | acceso remoto a servidores | remote server access |
| | `firma` | firma de aplicación | application signing |
| | `desconocido` | proveedor desconocido | unknown provider |
| | `no_aplica` | (no se muestra) | (not shown) |
| Reglas del agente (postura) | `allow` | lo permite | allows it |
| | `ask` | pide confirmación | asks first |
| | `deny` | lo bloquea (solo por regla) | blocks it (rule only) |
| | `sin_regla` | sin regla | no rule |
| | `no_determinada` | no determinadas | not determined |
| Ajeno a la tarea | `si` / `no` / `no_determinado` | sí / no / no determinado | yes / no / not determined |
| Nivel | `comprobado` | COMPROBADO | VERIFIED |
| | `potencial` | POTENCIAL | POTENTIAL |
| | `hipotesis` | HIPÓTESIS | HYPOTHESIS |

El motivo del nivel ("por qué") ya tiene sus siete textos fijos en español e inglés en `_TEXTO_MOTIVO` de `finding.py`; se reutilizan tal cual.

## 6. Código de salida

| Código | Cuándo |
|---|---|
| 0 | La revisión terminó y no hay ningún hallazgo comprobado (sin hallazgos, o solo potenciales e hipótesis). |
| 1 | La revisión terminó y hay al menos un hallazgo **comprobado** (acuerdo de la Historia 13). No significa que la herramienta falló: significa "hay algo grave". |
| 2 | No se pudo empezar: la carpeta no existe o no es una carpeta, o los argumentos están mal. Mensaje breve en la salida de errores, sin traza. |
| 3 | Error interno inesperado (propuesta; decisión pendiente de Alex, P5). Mensaje en la salida de errores: "Error interno de AgentReach; no se muestra un reporte parcial". |

- El código lo decide **la lista de hallazgos después de la autocomprobación** (la que baja de nivel un comprobado sin sustento), no el texto impreso.
- "No se pudo revisar" **no** cambia el código. Para quien quiera que sí, una opción futura `--estricto` (código 1 si hay entradas no revisadas); se anota, no se construye en el MVP.
- La línea "Código de salida: 1 (hay hallazgos comprobados)" aparece al final del reporte, porque en PowerShell el código no se ve a menos que se escriba `echo $LASTEXITCODE` (en `cmd`: `echo %ERRORLEVEL%`).
- Si quien lee cierra la tubería antes de tiempo (`agentreach . | Select-Object -First 5`), la escritura falla con `BrokenPipeError` o con `OSError [Errno 22]` en Windows. Se captura sin traza y el código de salida sigue siendo el calculado.
- Los errores van a la salida de errores (`stderr`), en el mismo idioma, sin color si no es una terminal y sin trazas de Python.

## 7. Sanitización de rutas y textos

Todo texto que viene del disco o de la persona (rutas, nombres de archivo, la carpeta que se pasó como argumento, textos que un detector copie) puede ser un ataque contra quien lee el reporte: un nombre de archivo con `ESC[2J` borra la pantalla, con un título de ventana falso engaña, con U+202E (que invierte el orden del texto) hace que `informe.txt` parezca `informe.exe` al revés, con un salto de línea falsifica una línea del reporte.

La limpieza actual (`limpiar_ruta` en `finding.py`) ya quita secuencias de escape, controles (`\x00-\x1f`, `\x7f-\x9f`) y la categoría de formato Unicode (`Cf`, que incluye los que invierten el texto y los de ancho cero) más separadores de línea y párrafo. Es una buena base. Propongo completarla así:

1. **Mostrar escrito en lugar de borrar** (decisión pendiente de Alex, P4). Cada carácter peligroso se reemplaza por su forma escrita visible: `\x1b`, `\n`, `\t`, `\u202e`, `\U000e0041`. Un nombre como `nota<U+202E>txt.exe` sale como `nota\u202etxt.exe`: la persona ve que pasa algo raro (muestra `docs/nota\u202etxt.exe` en las muestras). Si se borra en silencio, el nombre mostrado ya no es el real.
2. **Categorías que se escriben:** control (`Cc`), formato (`Cf`, incluye invertir texto y ancho cero), separadores de línea y párrafo (`Zl`, `Zp`), mitades de par sustituto sueltas (`Cs`), uso privado (`Co`), sin asignar (`Cn`) y cualquier espacio que no sea el espacio normal (`Zs` distinto de U+0020, como el espacio sin salto o el espacio ideográfico). Los emoji compuestos pierden su pegamento de ancho cero al mostrarse; es un costo aceptable en nombres de archivo.
3. **Dónde se aplica:** (a) al construir `Ruta` y `NoRevisado` (ya ocurre), y (b) **otra vez al imprimir**, a todo texto dinámico antes de ajustar y pintar (segunda barrera). Incluye la carpeta revisada y los mensajes de error que repiten una ruta.
4. **Última comprobación antes de escribir:** el texto final solo puede contener caracteres ESC que formen parte de una secuencia de color propia (`ESC[...m`). Si aparece cualquier otro, se eliminan todos los ESC y se sigue (la prueba de la sección 9 lo comprueba). Así, aunque una fuente nueva de texto olvide limpiar, la terminal no recibe nada ajeno.
5. **Largo máximo de un nombre: 1000 caracteres visibles.** Pasado eso se corta con una marca explícita `...[recortada: N caracteres]`. Es la única excepción a "no cortar rutas", pensada para un nombre hecho a propósito para llenar la pantalla.
6. **Línea de aviso:** si algún nombre se mostró escrito, sale una nota "Algunos nombres traían caracteres invisibles o de control; se muestran escritos como \uXXXX" (aparece en las muestras).
7. **Límite que no se resuelve:** letras de otros alfabetos que se parecen (la "а" cirílica que parece una "a") no se detectan. Se declara; marcar nombres con alfabetos mezclados queda para la fase 2.

## 8. Los textos del catálogo: hallazgos para la Historia 13

Al armar las muestras con `CATALOGO_EXPLICACIONES` encontré cosas que conviene arreglar cuando se escriba `reporting/texto.py`. Son del catálogo, no de este diseño; no toqué nada.

- Palabras que un novato no entiende y no se explican: "rote la clave" (rotar es cambiarla por una nueva y desactivar la vieja), "gestor de secretos", "ask / deny" en el texto de TH-7 (el reporte los llama `pide confirmación` y `bloquea`), "Unicode" en TH-12, "shell" en TH-8, "hook" en TH-14 (sí lo explica), "mínimo privilegio" en TH-3.
- El texto de TH-17 dice "en un archivo sin relación con la tarea" aunque el campo "ajeno a la tarea" sea "no" o "no determinado"; en las muestras el único TH-17 es el de `src/estilos/notas-tipografia.txt` (ajeno: sí) por eso. Conviene que el texto cambie según el campo o que diga "puede no tener relación con la tarea".
- El catálogo usa "usted"; el boceto HTML usa "tú" (decisión pendiente P3).
- La propuesta de vocabulario (`docs/vocabulario-es-en.md`) llama "posture" a la postura; en pantalla uso "Reglas del agente / Agent rules", como pide esa propia hoja.

## 9. Pruebas sugeridas (para el que escriba la Historia 13)

1. **Ancho:** con anchos 40, 60, 80 y 140, ninguna línea de texto plano supera `W - 1` (salvo una ruta indivisible más larga) y ninguna palabra queda partida (comparar contra el texto sin ajustar).
2. **Color:** con `NO_COLOR=1`, con salida no terminal y con `--color nunca` no sale ningún `ESC`; con `--color siempre` y 24 bits cada línea pintada termina en `ESC[0m`; sin color el texto es **idéntico** al de con color después de quitar los códigos.
3. **Siempre símbolo y palabra:** con color apagado cada nivel sigue mostrando su palabra; en modo ASCII no hay ningún carácter fuera de ASCII en los símbolos.
4. **Codificación:** un `io.TextIOWrapper` con `cp437` y otro con `cp1252` no lanzan `UnicodeEncodeError`; un nombre con mitad de par sustituto sale como `\udc80`.
5. **Sanitización:** nombres con `ESC[2J`, `ESC]0;titulo BEL`, `\n`, `\r`, U+202E, U+200B y U+E0041: el texto final no contiene ningún ESC ajeno, ningún salto de línea inventado, y los nombres salen escritos.
6. **Sin códigos en pantalla:** sin `--detalle`, ninguna salida contiene `TH-` seguido de número ni ninguno de los identificadores de motivo; con `--detalle` los contiene.
7. **Cobertura:** los 20 tipos y los 10 motivos tienen nombre legible en ambos idiomas (como la prueba a y k que ya pide la Historia 13).
8. **Estabilidad:** la fecha entra por un reloj inyectado (parámetro `ahora`), para que dos ejecuciones con el mismo reloj den texto idéntico (criterio e de la Historia 5b).
9. **Secretos:** una carpeta con valores canario no los deja salir en ninguna de las cuatro modalidades (color, sin color, ASCII, `--detalle`, ambos idiomas).

## 10. Muestras

Archivos en `docs/reporte-terminal/muestras/`, todos en UTF-8 sin marca de orden de bytes y con fin de línea `\n`:

| Archivo | Qué muestra |
|---|---|
| `muestra-1-es-color.ansi.txt` | Español, 80 columnas, **con color** de 24 bits (Paleta A) y símbolos Unicode. Contiene las secuencias de color; en un editor se ven como `[38;2;...m`. |
| `muestra-2-es-sin-color.txt` | Lo mismo sin color (como sale con `NO_COLOR` o al redirigir). |
| `muestra-3-es-ancho-60.txt` | Español, ancho mínimo 60, símbolos ASCII de respaldo. Ninguna línea pasa de 59 columnas; la ruta absoluta del encabezado queda sola en su línea. |
| `muestra-4-en.txt` | Inglés, 80 columnas, sin color. |

Datos: salen del proyecto de prueba (`C:\dev\proyecto-prueba-agentreach\proyecto`): `.env.local` y `.env.staging` (comprobados, PP-05 y PP-04), `.env` con la regla de bloqueo de Claude Code (PP-01), `.env.production` (PP-03), `enlace-externo` (EN-01), `src/estilos/notas-tipografia.txt` (AT-08), `AGENTS.md` (CX-02). **Los números de línea son inventados** para la maqueta (el proyecto de prueba no los fija en `respuestas-esperadas.md`) y el total de 41 archivos mirados también. Los niveles son los del oráculo salvo el de `enlace-externo`, cuyo motivo se muestra como "No determinado" porque la lista cerrada de motivos no tiene uno específico para enlaces. Ningún valor de secreto aparece (el modelo de datos no tiene dónde guardarlo) y ni siquiera los nombres de las variables: el `Finding` solo guarda proveedor, y el diseño no agrega nada que lo cambie.

Cómo verlas con color: Windows Terminal con PowerShell 7 (`pwsh`):

```powershell
Get-Content -Encoding UTF8 -Raw docs\reporte-terminal\muestras\muestra-1-es-color.ansi.txt | Write-Host -NoNewline
```

Qué **no** probé: que se vean bien en una consola real (solo verifiqué los bytes: ancho de cada línea, que no haya ESC ajenos, que no salga ningún `TH-n` ni identificador técnico, ni nada con forma de secreto). Los símbolos ■ ▲ ◊ ○ √ → conviene mirarlos en la consola de Alex antes de dar por cerrada la elección.

## 11. Qué cambiaría en la Historia 13

(Se resume también en la respuesta; no se editó la historia.)

1. **Nuevo comando y opciones:** agregar a "Qué hace" `--detalle`, `--idioma es|en|auto`, `--color auto|siempre|nunca`, `--ascii` y `--ancho` (esta última para pruebas), y el atajo `agentreach <carpeta>` que ya existe por 5b. Quitar la ambigüedad de que el reporte se escribe "por pantalla" solamente: decidir `--salida` (P8).
2. **Estructura del texto:** reemplazar "ordena por nivel" por la estructura de la sección 1: encabezado con carpeta absoluta y fecha, aviso de secretos, resumen arriba, grupos por nivel y por archivo, sección única "Qué no pudo revisar" con partes A y B.
3. **Compacto vs detalle:** definir que los códigos `TH-n` y los identificadores de motivo salen solo con `--detalle` (criterio nuevo: ninguna salida compacta los contiene).
4. **Catálogos nuevos en los dos idiomas:** título corto por tipo (20) y por motivo (10), proveedor, postura y nivel; extender la prueba de cobertura (a y k) a esos títulos y agregar el arreglo de las palabras sin explicar de la sección 8.
5. **Legibilidad y color como criterios medibles:** ancho `clamp(60, 100)`, ajuste en límites de palabra, rutas indivisibles y relativas, color solo con terminal y sin `NO_COLOR`, siempre palabra y símbolo, ASCII de respaldo.
6. **Codificación y sanitización:** `reconfigure` seguro dentro de `main()`, salida escrita de una vez, caracteres peligrosos mostrados escritos con la segunda barrera al imprimir y la comprobación final de ESC.
7. **Códigos de salida:** mantener 0 y 1; confirmar 2 para carpeta inválida y decidir 3 para error interno; que el código salga de la lista corregida por la autocomprobación.
8. **Dos conflictos a resolver antes de implementar:** (a) la fecha del encabezado rompe "dos ejecuciones dan texto idéntico" (5b, criterio e) si no se inyecta un reloj; (b) `Finding` y `NoRevisado` guardan la ruta **ya limpia**, pero la autocomprobación de la Historia 13 reabre el archivo por esa ruta: un archivo cuyo nombre trae caracteres de control no se encontraría. Conviene guardar la ruta real aparte de la ruta para mostrar.
