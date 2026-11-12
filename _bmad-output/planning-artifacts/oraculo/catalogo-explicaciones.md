---
title: "AgentReach — Catálogo de explicaciones (\"qué significa\")"
type: catalog
status: draft
created: 2026-11-06
companion: checklist-oraculo.md (mismos IDs)
nature: texto fijo y determinista; no usa modelo de lenguaje; no contiene valores de secretos
---

# Catálogo de explicaciones

Una explicación fija por cada tipo de hallazgo del checklist, escrita para una persona que no conoce los términos técnicos. Cada texto responde, en 2 a 4 frases: **qué es**, **para qué sirve**, **qué podría hacer un agente que llegue a ello** y **qué hacer**. Los términos técnicos se definen la primera vez que aparecen y todos están en el glosario del final.

Reglas del catálogo:
- El texto es el mismo siempre para el mismo ID. Los datos propios de cada hallazgo (ruta, nivel, regla) los pone el reporte en otros campos, no este texto.
- Ningún texto contiene ni cita un valor de secreto.
- "Un agente que llegue a ello" significa: un agente de IA que, con los permisos con que corre, pueda abrir ese archivo o usar esa herramienta. Que **pueda** no significa que lo haya hecho.
- Las acciones sugeridas son recomendaciones. AgentReach no las ejecuta: solo lee y avisa.
- Una nota sobre palabras: un **agente de IA** es un programa que, además de conversar, ejecuta acciones por ti (leer archivos, correr comandos, usar servicios).

---

## A. Tokens y credenciales de nube y de plataformas

### CK-001 — Credenciales de AWS
AWS es un servicio de **nube**, es decir, computadoras y almacenamiento que se alquilan por internet. Sus **credenciales** (el equivalente a un usuario y una contraseña para programas) permiten crear, cambiar o borrar esos recursos y generar costos. Un agente que las lea podría actuar en tu cuenta de AWS con los mismos permisos que tú. Conviene que el agente no pueda llegar a esa carpeta y que las credenciales tengan los permisos mínimos necesarios.

### CK-002 — Credenciales de Azure
Azure es la nube de Microsoft. Estas credenciales son la llave con la que tus programas entran a tu cuenta y a sus recursos, como máquinas, bases de datos y almacenamiento. Un agente que las alcance podría leer datos o cambiar y borrar recursos. Revisa quién las puede leer y usa cuentas de servicio con permisos acotados.

### CK-003 — Credenciales de Google Cloud
Google Cloud es la nube de Google. Los archivos de credenciales, a veces de una **cuenta de servicio** (una cuenta pensada para que la use un programa y no una persona), dan acceso a sus recursos. Un agente que los lea podría usar tu proyecto de Google Cloud, con costos o con pérdida de datos. Guárdalos fuera de los proyectos y limita sus permisos.

### CK-004 — Tokens de plataformas de despliegue y alojamiento
Un **token** es una cadena larga que funciona como contraseña de un programa: quien lo tiene puede actuar como tú en un servicio sin que te lo pidan de nuevo. Plataformas como Railway, Vercel, Netlify, Fly.io, Heroku o Cloudflare alojan sitios y bases de datos, y su token suele permitir publicar y también borrar. Un agente que lo encuentre podría cambiar o eliminar un entorno de **producción** (la versión real y en uso de una aplicación). Guarda el token fuera del proyecto y usa uno con alcance limitado.

### CK-005 — Tokens de alojamiento de código
GitHub, GitLab o Bitbucket guardan tu código en un **repositorio** (una carpeta de proyecto con su historial de cambios). Un token personal permite leer o modificar esos repositorios sin tu contraseña. Un agente que lo alcance podría descargar código privado, subir cambios o borrar ramas. Revoca el token si estuvo a la vista y crea uno con los permisos mínimos y con fecha de vencimiento.

### CK-006 — Claves de API de proveedores de IA
Una **clave de API** es una credencial que permite usar un servicio por programa, aquí un servicio de inteligencia artificial. Quien la tenga puede hacer consultas a tu nombre y generar gasto en tu cuenta. Un agente que la lea podría usarla o copiarla a otro lugar. Guárdala en el almacén del sistema o en una variable, no en archivos del proyecto, y establece un límite de gasto.

### CK-007 — Claves de servicios SaaS (pagos, mensajería, correo, chat)
SaaS son servicios en internet que usas sin instalarlos, como pagos, envío de correo o mensajería. Sus claves permiten operar en esas cuentas: cobrar, enviar mensajes o leer conversaciones. Un agente que las alcance podría enviar correos o mensajes en tu nombre, o mover dinero si es una clave de producción. Separa las claves de prueba de las reales y guarda las reales fuera del proyecto.

### CK-008 — Cadenas de conexión de bases de datos
Una **base de datos** guarda la información de una aplicación. Una cadena de conexión es el texto que dice dónde está y con qué usuario y contraseña entrar. Un agente que la lea podría consultar, cambiar o borrar esos datos. Si apunta a una base real, cámbiala por una cuenta de solo lectura o quítala del proyecto.

### CK-009 — Configuración de Kubernetes (kubeconfig)
Kubernetes es un sistema que ejecuta aplicaciones en muchos servidores; el archivo **kubeconfig** guarda a qué clústeres (conjuntos de servidores) puedes entrar y con qué credenciales. Un agente que lo lea podría desplegar, cambiar o borrar aplicaciones en esos servidores. Usa credenciales de corta duración y mantén el archivo fuera del alcance del agente.

### CK-010 — Credenciales y estado de Terraform y herramientas similares
Terraform describe en archivos la infraestructura de nube (servidores, redes, bases de datos) y la crea automáticamente. Su archivo de **estado** puede contener contraseñas en texto legible, y sus credenciales permiten rehacer o destruir esa infraestructura. Un agente que lo alcance podría ver secretos o ejecutar cambios masivos. No guardes el estado en el proyecto y limita quién puede ejecutar la herramienta.

### CK-011 — Secretos de firma y de sesión de aplicaciones
Estos valores sirven para que una aplicación firme sus sesiones o cifre datos. Quien los conozca puede fabricar sesiones válidas, es decir, hacerse pasar por cualquier usuario. Un agente que los lea podría comprometer la aplicación entera. Cámbialos si estuvieron expuestos y guárdalos fuera del código.

### CK-012 — Credenciales exportadas o de cuenta de servicio sin nombre fijo
Son archivos descargados de un servicio que contienen credenciales completas, normalmente en formato **JSON** (un formato de texto estructurado), con nombres como `credentials.json` o `token.json`. Dan el mismo acceso que la cuenta que las generó. Un agente que los abra podría usar esa cuenta. Bórralos del proyecto si no son necesarios, revoca los que estuvieron expuestos y guarda los vigentes en un almacén seguro.

## B. Claves privadas, certificados y firmas

### CK-013 — Claves privadas SSH
**SSH** es una forma segura de conectarse a otra computadora o a un servicio como GitHub sin escribir contraseña. Funciona con un par de claves: la **pública**, que se puede compartir, y la **privada**, que es el secreto y no debe salir de tu equipo. Un agente que lea la clave privada podría entrar a los servidores y repositorios a los que ella da acceso. Protégela con frase de contraseña y mantenla fuera del alcance del agente.

### CK-014 — Configuración SSH, agente SSH y listas de hosts
Estos archivos dicen a qué servidores te conectas y con qué clave. El **agente SSH** es un programa que mantiene tus claves desbloqueadas en memoria para que no tengas que escribir la frase cada vez. Un agente de IA con acceso a ese programa podría usar tus claves sin leer el archivo de la clave. Descarga las claves del agente SSH cuando no las uses y revisa a qué servidores apunta la configuración.

### CK-015 — Claves privadas y almacenes de claves genéricos
Son archivos como `.pem`, `.key`, `.pfx`, `.p12`, `.jks` o `.ppk` que contienen una clave privada o un conjunto de claves y certificados. Sirven para firmar, cifrar o identificar un servidor o una persona. Un agente que los lea podría hacerse pasar por ti o por tu servidor. Muévelos a un almacén protegido, y busca la contraseña asociada, que a veces está en un archivo vecino.

### CK-016 — Claves GPG y de firma
**GPG** es un programa para firmar y cifrar mensajes y cambios de código con un par de claves. La clave privada demuestra que algo lo hiciste tú. Un agente que la alcance podría firmar contenido a tu nombre. Protégela con frase de contraseña y mantén esa carpeta fuera del alcance del agente.

## C. Archivos `.env` y configuración con secretos

### CK-017 — Archivos `.env` y variantes
Un archivo `.env` es una lista de ajustes de una aplicación (por ejemplo contraseñas y tokens) que se guarda junto al proyecto. Es la ubicación más común de secretos en un proyecto. Un agente que trabaje en esa carpeta lo puede leer con facilidad, incluso si la tarea no tiene relación. Mantén los secretos fuera del proyecto o con acceso restringido, y no subas el archivo al repositorio.

### CK-018 — Archivos de configuración de aplicación con secretos
Muchas aplicaciones guardan sus ajustes en archivos como `appsettings.json` o `config.yml`, a veces con contraseñas o claves dentro. Visual Studio ofrece además un almacén llamado User Secrets, fuera del proyecto, pensado para evitarlo. Un agente que lea estos archivos podría obtener esas claves. Mueve los secretos a un almacén fuera del repositorio y deja en el archivo solo ajustes que no sean secretos.

### CK-019 — Docker y Compose con secretos embebidos
**Docker** empaqueta una aplicación en un contenedor, una caja aislada que se puede copiar a otro equipo; **Compose** describe varios contenedores en un archivo. Si ese archivo trae contraseñas escritas, cualquiera que lo vea las tiene. Un agente que lo lea podría usarlas. Pásalas por variables o por el sistema de secretos de Docker en lugar de escribirlas en el archivo.

### CK-020 — Archivos de secretos dedicados
Son archivos creados para guardar secretos, como `secrets.yaml`, `*.tfvars`, `.pgpass` o `.vault-token`. A veces están cifrados y a veces no. Un agente que los alcance podría leer contraseñas, o usar el token de un gestor de secretos. Verifica si están cifrados, protégelos con permisos estrictos y sácalos del proyecto.

### CK-021 — Perfiles de publicación y archivos de despliegue de Visual Studio
Visual Studio guarda en archivos como `.pubxml` y `.PublishSettings` los datos para publicar una aplicación en un servidor, a veces con usuario y contraseña. Un agente que los lea podría publicar o cambiar esa aplicación. Deja las contraseñas fuera del archivo y no subas los perfiles personales al repositorio.

### CK-022 — Copias de seguridad, volcados y exportaciones
Son copias de una base de datos o de archivos (`.sql`, `.bak`, `.dump`, `.zip`). Pueden contener datos personales, contraseñas y secretos de toda la aplicación. Un agente que las abra obtiene mucho más de lo que necesita para cualquier tarea. Guárdalas en un lugar protegido y fuera del proyecto, y bórralas cuando ya no hagan falta.

## D. Credenciales de herramientas de línea de comandos (CLI)

### CK-023 — GitHub CLI (`gh`)
Una **CLI** es una herramienta que se maneja escribiendo comandos en una terminal; `gh` es la de GitHub. Cuando inicias sesión, guarda una credencial para no pedírtela de nuevo, en un archivo o en el almacén del sistema. Un agente podría usar `gh` ya conectado para actuar en GitHub sin leer ningún archivo. Cierra la sesión cuando no la necesites o usa una cuenta con permisos limitados.

### CK-024 — Docker (`config.json`)
Este archivo recuerda con qué cuentas iniciaste sesión en registros de imágenes de Docker (lugares donde se guardan los contenedores). Puede guardar la credencial en un formato que parece cifrado pero se deshace fácilmente (base64), o delegar en el almacén del sistema. Un agente que lo lea podría descargar o subir imágenes con tu cuenta. Prefiere el almacén del sistema y revoca los tokens que estuvieron expuestos.

### CK-025 — npm, Yarn y pnpm
Son gestores de paquetes de JavaScript: descargan y publican bibliotecas de código. Su archivo de ajustes `.npmrc` puede traer un token que permite publicar paquetes a tu nombre. Un agente que lo lea podría publicar una versión alterada de un paquete tuyo. Guarda el token en una variable o en el almacén del sistema y usa tokens con permiso solo de lectura cuando puedas.

### CK-026 — PyPI, pip, uv y twine
Son las herramientas de Python para instalar y publicar paquetes. Sus archivos de ajustes pueden contener el token para publicar o la dirección de un repositorio privado con usuario y contraseña. Un agente que los lea podría publicar paquetes a tu nombre o acceder a un repositorio privado. Usa tokens acotados y no los guardes en archivos del proyecto.

### CK-027 — NuGet, Maven, Gradle y Cargo
Son los gestores de paquetes de .NET, Java y Rust. Sus archivos de ajustes pueden contener contraseñas o tokens para descargar o publicar paquetes. Un agente que los lea podría publicar o descargar código privado con tu cuenta. Usa tokens de alcance limitado y fuera del proyecto.

### CK-028 — Credenciales de Git, `.netrc` y Windows Credential Manager
**Git** es el programa que lleva el historial de cambios de un proyecto. Puede recordar tus contraseñas en un archivo de texto plano (`.git-credentials`, `.netrc`) o en el Administrador de credenciales de Windows, que es un almacén del sistema. Un agente que lea el archivo podría usar la credencial, y uno que ejecute `git` podría autenticarse con el almacén sin que veas nada. Prefiere el almacén del sistema y evita el archivo de texto plano.

### CK-029 — Credenciales propias de los agentes (Claude Code y opencode)
Claude Code y opencode son agentes de IA que corren en tu equipo y guardan, en carpetas propias, la sesión de tu cuenta y claves de API. Estos archivos pueden dar acceso a tu cuenta del servicio de IA y a servidores conectados. Un agente (o cualquier programa) con acceso al disco podría leerlos. Revisa quién puede leer esas carpetas y no los copies a otros equipos.

## E. Variables de entorno sensibles

### CK-030 — Variables de entorno con nombre de credencial
Una **variable de entorno** es un ajuste con nombre que el sistema entrega a cada programa que arranca. Algunas llevan contraseñas o tokens, y se reconocen por nombres como `TOKEN`, `SECRET` o `KEY`. Los programas que lanza un agente suelen heredarlas, así que el agente puede usarlas sin abrir ningún archivo. Quita las variables que no necesites y evita dejar secretos permanentes en el entorno del usuario.

### CK-031 — Valores escritos en perfiles de shell
Un **perfil de shell** es un archivo que la terminal ejecuta cada vez que se abre y donde la gente suele definir variables. Si ahí hay secretos escritos, quedan activos en todas las terminales. El agente los hereda en cada comando que ejecute. Mueve los secretos a un almacén y deja en el perfil solo ajustes que no lo sean.

### CK-032 — Variables que apuntan a ubicaciones de credenciales o a configuración del agente
Algunas variables no contienen un secreto, pero indican dónde está: por ejemplo la ruta de un archivo de credenciales o de la carpeta de ajustes de un agente. Un agente podría seguirlas y llegar a algo que no se ve en el proyecto. Es una señal indirecta, por lo que AgentReach la marca como una hipótesis. Verifica a dónde apunta cada una y si ese destino debería ser accesible para el agente.

### CK-033 — Tokens de GitHub heredados por el agente
GitHub usa variables como `GITHUB_TOKEN` o `GH_TOKEN` para identificar a quien llama. Claude Code tiene una opción de limpieza del entorno, pero deja estas variables a propósito para que `gh` siga funcionando. Un agente puede, por tanto, ver y usar ese token aunque la limpieza esté activada. Si no la necesitas, no la definas de forma permanente y usa un token de alcance limitado.

## F. Archivos de contexto e instrucciones que un agente obedecería

### CK-034 — `CLAUDE.md`, `CLAUDE.local.md` y reglas de Claude Code
Son archivos de texto con instrucciones que Claude Code lee al empezar y suele seguir, como las convenciones del proyecto. Sirven para orientarlo, pero no lo limitan. Si alguien con acceso al proyecto escribe ahí algo malintencionado, el agente puede obedecerlo. Revísalos como revisarías un programa: de dónde vienen y qué piden. opencode también los lee.

### CK-035 — `AGENTS.md` y reglas de opencode
Es un archivo de instrucciones para agentes, equivalente al anterior, que opencode y otros leen al empezar. Un agente puede tomar sus órdenes como si fueran tuyas. No impone límites técnicos: solo orienta. Revisa su contenido y de dónde proviene, sobre todo si el repositorio es de otra persona.

### CK-036 — Skills (habilidades) del agente
Un **skill** es una carpeta con instrucciones y herramientas que enseñan al agente a hacer una tarea concreta. Puede declarar herramientas que el agente usa sin pedir confirmación y puede incluir **hooks** (programas que se ejecutan automáticamente ante ciertos eventos). Por eso un skill puede ampliar lo que el agente hace sin preguntarte. Revisa de dónde viene cada skill y qué herramientas aprueba por adelantado. opencode también lee los skills de Claude Code.

### CK-037 — Agentes y subagentes definidos
Un **subagente** es un agente auxiliar con su propio papel, instrucciones y permisos. Su definición puede darle herramientas, servidores y hooks propios, y cambiar lo que le piden confirmar. Un agente definido con permisos amplios actúa con más libertad de la que supones. Revisa sus permisos y de dónde proviene el archivo.

### CK-038 — Comandos y prompts personalizados
Son atajos con nombre que ejecutan un texto de instrucciones guardado en un archivo. Sirven para repetir tareas. Un comando de origen desconocido podría pedir al agente algo que tú no pretendías. Revisa el contenido antes de usarlo.

### CK-039 — Archivos de instrucciones de otras herramientas de IA
Otras herramientas de IA tienen sus propios archivos de reglas (por ejemplo para Cursor, Copilot o Gemini). Si esa herramienta está instalada, lee el archivo y suele seguirlo. Su presencia indica qué agentes pueden estar trabajando en el proyecto. Revisa su contenido igual que el de `CLAUDE.md`.

### CK-040 — Instrucciones sospechosas dentro de documentos, código o datos
Un texto cualquiera (README, documentación, comentarios, una página web) puede contener frases dirigidas a una IA, como "ignora tus instrucciones anteriores" u órdenes de leer archivos secretos. Esto se llama **inyección de instrucciones** y funciona porque el agente no siempre distingue entre datos que lee y órdenes que recibe. Un agente que las obedezca podría filtrar secretos o ejecutar comandos. Elimina el texto, no confíes en documentos de origen desconocido y limita lo que el agente puede hacer sin preguntar.

## G. Configuración del agente: permisos, hooks, MCP, plugins

### CK-041 — Reglas de permisos de Claude Code
Son las reglas que dicen qué puede hacer el agente sin preguntar (permitir), qué debe consultar (preguntar) y qué no puede hacer (denegar). Una regla muy amplia, como permitir todos los comandos, le deja actuar sin tu confirmación. Una regla de denegar protege de las herramientas del agente, pero no es una barrera del sistema operativo: un programa que el agente ejecute puede no estar cubierto. Revisa que lo permitido sea lo mínimo y trata las reglas de denegar como una capa de ayuda, no como garantía.

### CK-042 — Modo por defecto y confianza del espacio de trabajo
El **modo** decide cuánto pregunta el agente: desde pedir confirmación a casi todo hasta no preguntar nada. El modo "sin permisos" o el automático hacen que actúe sin consultarte. Además, el agente solo aplica las reglas de permitir de un proyecto después de que aceptes confiar en esa carpeta. Elige el modo más estricto que te resulte práctico y acepta la confianza solo en proyectos que conozcas.

### CK-043 — Sandbox de Claude Code ausente o no aplicable
Un **sandbox** es una caja aislada que limita lo que un programa puede tocar en el equipo. En Windows (sin WSL2), Claude Code no lo ofrece, así que los comandos que ejecuta tienen los mismos permisos que tú. Aunque exista, solo cubre los comandos de terminal y no a todo el agente. Si necesitas ese aislamiento, considera usar WSL2 o una máquina virtual.

### CK-044 — Política gestionada de Claude Code
Una **política gestionada** es una configuración que un administrador fija y que el usuario no puede cambiar; sirve para imponer reglas en una empresa. Si existe, manda sobre todo lo demás. En un equipo personal lo normal es que no haya ninguna, y eso no es un error. Verifica de dónde viene si aparece una y quién la administra.

### CK-045 — Hooks de Claude Code
Un **hook** es un programa o comando que se ejecuta solo cuando ocurre algo en el agente, por ejemplo antes de usar una herramienta. Corre con tu acceso completo, sin las limitaciones del agente. Un hook de origen desconocido podría ejecutar cualquier cosa en tu equipo. Revisa qué hace cada hook y de qué archivo de ajustes proviene.

### CK-046 — Servidores MCP de Claude Code
**MCP** es un estándar para conectar a un agente con herramientas y servicios externos. Un servidor MCP local es un programa que arranca en tu equipo con tu acceso completo y recibe, por defecto, tus variables de entorno. Un archivo `.mcp.json` dentro de un repositorio ajeno puede arrancarse sin preguntar si el agente se usa en modo no interactivo. Revisa cada servidor, qué programa ejecuta y qué variables recibe.

### CK-047 — Herencia de entorno y bloque `env` en Claude Code
El bloque `env` de los ajustes define variables que verá todo lo que lance el agente. Una opción de limpieza quita credenciales de esos programas, pero está desactivada por defecto y no cubre todo. Si hay secretos en el entorno, el agente y sus herramientas los verán. Activa la limpieza si te sirve, y mantén los secretos fuera de los ajustes.

### CK-048 — Permisos de opencode
opencode usa su propio archivo de reglas, donde casi todo está permitido por defecto y solo se pide confirmación en unos pocos casos. A diferencia de Claude Code, gana la última regla que coincide, no la de denegar. Una regla de denegar la lectura podría no cubrir los comandos de terminal: está por verificar. Revisa las reglas y no asumas que denegar equivale a proteger.

### CK-049 — Capas de configuración de opencode y referencias a secretos
opencode combina ajustes de varios lugares, y el de mayor precedencia gana. Los ajustes pueden apuntar a una variable o a un archivo para traer valores. Si ese archivo contiene un secreto, el agente puede alcanzarlo por esa vía. Revisa qué capas existen y a dónde apuntan las referencias.

### CK-050 — Plugins y dependencias de opencode
Un **plugin** es un programa que amplía a la herramienta y se ejecuta al arrancar, con tus permisos. Puede observar o cambiar lo que hace el agente, y descargar dependencias. Un plugin de origen desconocido puede hacer cualquier cosa en tu equipo. Revisa su origen y qué hace cada uno.

### CK-051 — Servidores MCP de opencode
Como en Claude Code, un servidor MCP local es un programa que se ejecuta en tu equipo con tu acceso. Puede recibir variables con credenciales, y sus sesiones guardan tokens en un archivo propio. Un servidor de origen desconocido puede hacer cualquier cosa. Revisa qué programa ejecuta cada uno y qué variables recibe.

### CK-052 — Exposición de red y compartición de sesiones de opencode
opencode puede arrancarse como servidor que escucha en la red, y puede compartir sesiones por una página web. Si se abre a toda la red sin contraseña, otras personas podrían manejar el agente o ver la conversación. El comportamiento por defecto de compartir está por verificar. Si usas el modo servidor, fija una contraseña y limita la red; desactiva compartir si no lo necesitas.

## H. Scripts de despliegue, CI e infraestructura

### CK-053 — Scripts de despliegue y operaciones
Son programas pequeños que publican una aplicación, cambian una base de datos o deshacen un cambio. Usan las credenciales que haya en el equipo. Un agente que los ejecute, aunque sea por una tarea inocente, podría tocar el entorno real, incluso borrar. Revisa qué entorno toca cada script y evita que el agente pueda ejecutarlos sin tu confirmación.

### CK-054 — Workflows de CI/CD
**CI/CD** son procesos automáticos que prueban y publican el código cada vez que se sube un cambio, descritos en archivos como los de `.github/workflows`. Corren en servidores con los secretos del repositorio. Un agente que pueda editar y subir estos archivos podría hacer que ese proceso ejecute pasos con esos secretos. Guarda los secretos solo en el almacén del servicio, y exige revisión humana para cambios en estos archivos.

### CK-055 — Manifiestos de infraestructura y Kubernetes con secretos
Un **manifiesto** es un archivo que describe lo que debe existir en un servidor o clúster. Los secretos de Kubernetes se guardan allí en base64, que parece cifrado pero se deshace al instante. Un agente que lo lea obtiene los secretos. Usa un gestor de secretos, y no versiones manifiestos con valores reales.

### CK-056 — Scripts de ciclo de vida y tareas del editor
Algunos proyectos ejecutan comandos automáticamente al instalar o compilar (por ejemplo `postinstall` o las tareas de un editor). Corren con tus permisos y sin que lo notes. Un agente que ejecute una instalación normal podría activar un comando de ese tipo. Revisa lo que ejecutan, sobre todo en proyectos que no escribiste.

## I. Registros, historial y datos del agente

### CK-057 — Transcripciones de Claude Code
Una **transcripción** es el registro completo de una sesión con el agente: lo que se dijo, los archivos que leyó y lo que imprimieron los comandos. Se guarda en texto plano, así que si el agente leyó un secreto, queda copiado ahí. Otro programa o agente con acceso a esa carpeta podría leerlo. Reduce el tiempo de retención, protege la carpeta y bórralas cuando ya no las necesites.

### CK-058 — Otros datos de Claude Code (historial, copias, cachés)
Además de las transcripciones, el agente guarda lo que escribes, copias anteriores de los archivos que modificó, contenido pegado y una foto del entorno de la terminal. Todo puede contener datos sensibles, incluidos archivos de configuración editados. Un programa con acceso a esa carpeta podría leerlos. Limita la retención y protege la carpeta.

### CK-059 — Datos y base de sesiones de opencode
opencode guarda sus sesiones en una base de datos local (SQLite, un archivo que contiene tablas), además de registros, instantáneas y archivos de credenciales. Pueden incluir contenido de archivos y comandos. Un programa con acceso a esa carpeta podría leerlos. Revisa el contenido que se acumula, protege la carpeta y limpia lo que no necesites.

### CK-060 — Volcados de memoria y snapshots de depuración
Un **volcado de memoria** es una foto de lo que un programa tenía en memoria al fallar o al pedirlo. Puede incluir conversaciones y credenciales en texto legible. Un agente o persona que lo abra podría extraerlas. Bórralos cuando termines de depurar y no los compartas.

## J. Git y repositorio

### CK-061 — Remotos de Git con credenciales embebidas
Un **remoto** es la dirección del servidor donde Git sube y baja el código. Si esa dirección lleva usuario y token escritos, cualquier comando de Git del agente se autentica con ellos. Quien lea el archivo de configuración del repositorio los obtiene. Cambia la dirección por una sin credenciales, usa el almacén del sistema y revoca el token.

### CK-062 — Secretos versionados y `.gitignore` insuficiente
Un archivo está **versionado** cuando Git lo guarda en el historial. Si un secreto se versionó, queda en el historial aunque luego lo borres. `.gitignore` es el archivo que le dice a Git qué no guardar; si no cubre los secretos, es fácil subirlos por error. Un agente puede leer el historial completo. Revoca cualquier secreto versionado y completa `.gitignore`.

### CK-063 — Hooks de Git activos
Los hooks de Git son programas que se ejecutan solos al guardar o subir cambios. Corren con tus permisos, también cuando los dispara el agente. Un hook de origen desconocido podría ejecutar comandos. Revisa los hooks activos y a qué carpeta apunta la configuración.

### CK-064 — Submódulos y árboles de trabajo que apuntan fuera del repo
Un **submódulo** es un repositorio dentro de otro, y un **árbol de trabajo** es una segunda copia de un proyecto en otra carpeta. Pueden hacer que el proyecto incluya carpetas que están fuera de su ubicación. El agente podría trabajar con ellas sin que lo notes. Revisa dónde están esas carpetas y qué contienen.

## K. Alcance de rutas y sistema de archivos

### CK-065 — Symlinks y junctions que salen del repo
Un **symlink** (enlace simbólico) y una **junction** (enlace de carpeta de Windows) son accesos directos a nivel del sistema: una carpeta del proyecto que en realidad muestra otra ubicación. Si una apunta fuera del proyecto, el agente puede llegar a esa carpeta creyendo que sigue en el proyecto. Puede exponer archivos que no deberían estar a su alcance. Elimina el enlace o revisa a dónde lleva.

### CK-066 — Directorios adicionales concedidos al agente
Algunos agentes permiten añadir carpetas extra donde pueden leer sin pedir confirmación. Cada una amplía lo que el agente alcanza más allá del proyecto. Una carpeta amplia, como todo el perfil de usuario, expone todo lo que contiene. Reduce la lista a lo necesario.

### CK-067 — Rutas de red y unidades mapeadas
Una **ruta de red** (UNC) apunta a una carpeta en otra computadora, y una **unidad mapeada** es una letra (como `Z:`) que representa una carpeta de red. Acceder a una ruta de red puede enviar tus credenciales de Windows a esa otra computadora. El agente podría leer carpetas compartidas que no sabías que alcanzaba. Revisa qué unidades tienes montadas y si el agente debe llegar a ellas.

### CK-068 — Carpetas sincronizadas con la nube
Servicios como OneDrive o Dropbox copian tus carpetas a internet y a tus otros equipos. Un secreto en una carpeta sincronizada también existe en esas copias. Un agente en otro equipo de la misma cuenta podría llegar a él. Mueve los proyectos con secretos fuera de las carpetas sincronizadas.

### CK-069 — Directorio de trabajo demasiado amplio
El **directorio de trabajo** es la carpeta desde la que se inicia el agente, y suele ser la zona donde lee sin pedir confirmación. Si lo abres en una carpeta que contiene muchos proyectos, o en todo el perfil, el agente alcanza los secretos de todos. Es una causa frecuente de que un agente toque archivos ajenos a su tarea. Abre el agente en la carpeta del proyecto concreto.

### CK-070 — Permisos del sistema demasiado abiertos sobre archivos sensibles
Cada archivo tiene una lista de quién puede leerlo, llamada **ACL** (lista de control de acceso) en Windows y permisos de modo en Linux y macOS. Si un archivo con claves es legible por muchas cuentas, cualquiera de ellas, incluidos programas que corran con esas cuentas, puede abrirlo. Los permisos del sistema son la única barrera real frente a un agente. Restringe el archivo al usuario que lo necesita.

## L. Falsos positivos conocidos

Un **falso positivo** es un aviso que parece un secreto pero no lo es. AgentReach los informa igualmente, con una nota, para que tú decidas.

### FP-001 — Archivos de plantilla de variables
Archivos como `.env.example` listan los nombres de los ajustes que una aplicación necesita, sin los valores reales. Sirven de guía para quien configura el proyecto. No son un riesgo si de verdad están vacíos o con valores de relleno. Verifica que no contengan valores reales.

### FP-002 — Claves de ejemplo de la documentación del proveedor
Los proveedores publican claves de ejemplo en su documentación, que no sirven para nada real. Suelen incluir la palabra `EXAMPLE`. No son un riesgo. Confirma que sean exactamente las del manual y no una clave real.

### FP-003 — Fixtures, mocks y datos de prueba
Un **fixture** es un dato falso preparado para las pruebas automáticas de un proyecto. Los secretos de esas carpetas suelen ser inventados. No son un riesgo si son falsos. Confirma que ninguno sea real.

### FP-004 — Valores de marcador de posición o de desarrollo local
Valores como `changeme`, `password` o `localhost` son relleno evidente o apuntan al propio equipo. No dan acceso a ningún servicio real. Verifica que no se usen también en un entorno real.

### FP-005 — Referencias a un secreto sin valor
Un texto como `${VAR}` o `secrets.NOMBRE` solo dice dónde buscar un valor, no lo contiene. Es la forma correcta de no escribir secretos. No es un riesgo por sí mismo. Revisa dónde se guarda el valor real.

### FP-006 — Material público: claves públicas y certificados
Las claves públicas (`.pub`) y los certificados sin clave privada están hechos para compartirse. No dan acceso a nada. Confirma que el archivo no incluya además la clave privada.

### FP-007 — Sumas de verificación y hashes de integridad
Son cadenas largas de aspecto aleatorio que sirven para comprobar que un archivo no cambió. No son contraseñas. No requieren acción.

### FP-008 — Código de terceros y salidas de compilación
Carpetas como `node_modules` o `.venv` contienen código ajeno e instalado, con ejemplos que parecen secretos. Normalmente no son los tuyos. Confirma que no haya archivos tuyos mezclados.

### FP-009 — Hooks de ejemplo de Git
Git trae ejemplos de hooks con extensión `.sample` que no se ejecutan. No son un riesgo. Solo importan los hooks sin esa extensión.

### FP-010 — Nombres que coinciden con el patrón pero no son secretos
Palabras como `KEY` o `token` aparecen en nombres que no tienen que ver con credenciales (por ejemplo una clave de diccionario). No hay un secreto ahí. Confirma que el valor no tenga forma de credencial.

### FP-011 — Documentos y pruebas del propio proyecto AgentReach
Los documentos y datos de prueba de AgentReach mencionan nombres de secretos para explicarlos. No contienen valores reales. No requieren acción.

### FP-012 — Archivos de configuración o de contexto inocuos
Un archivo de ajustes vacío o con solo convenciones de estilo no cambia lo que el agente puede hacer. Es un hallazgo de inventario, no de riesgo. Verifica que su contenido siga siendo inocuo.

---

## Glosario

Definiciones fijas, ordenadas alfabéticamente.

- **ACL (lista de control de acceso):** lista, asociada a un archivo o carpeta en Windows, de quién puede leerlo, cambiarlo o ejecutarlo. En Linux y macOS algo equivalente son los permisos de modo.
- **Agente de IA:** programa que usa inteligencia artificial para ejecutar acciones por ti, como leer archivos, correr comandos o usar servicios.
- **Agente SSH:** programa que mantiene tus claves SSH desbloqueadas en memoria para no pedir la frase de contraseña cada vez.
- **API / clave de API:** forma en que un programa usa otro servicio; la clave es la credencial que lo autoriza.
- **Base de datos:** lugar donde una aplicación guarda su información de forma ordenada.
- **Base64:** forma de escribir datos que parece ilegible pero se deshace al instante; no es cifrado.
- **CI/CD:** procesos automáticos que prueban y publican código cada vez que se sube un cambio.
- **CLI (herramienta de línea de comandos):** programa que se maneja escribiendo comandos en una terminal.
- **Clave privada / clave pública:** par de claves; la pública se puede compartir y la privada es el secreto que no debe salir de tu equipo.
- **Contenedor (Docker):** caja aislada con una aplicación y lo que necesita para correr.
- **Credencial:** dato (contraseña, token, clave) que demuestra quién eres ante un programa o servicio.
- **Directorio de trabajo:** carpeta desde la que se inicia el agente, donde suele leer sin pedir confirmación.
- **`.env`:** archivo con ajustes de una aplicación, a menudo con contraseñas y tokens.
- **Falso positivo:** aviso que parece un secreto pero no lo es.
- **Fixture:** dato falso preparado para pruebas automáticas.
- **Git:** programa que guarda el historial de cambios de un proyecto.
- **GPG:** programa para firmar y cifrar con un par de claves.
- **Hook:** programa que se ejecuta automáticamente cuando ocurre un evento.
- **Inyección de instrucciones:** texto escondido en un documento que intenta que una IA lo obedezca como si fuera una orden.
- **JSON:** formato de texto estructurado muy usado en archivos de configuración.
- **Junction:** acceso directo de carpeta del sistema de archivos de Windows.
- **Kubernetes / kubeconfig:** sistema que ejecuta aplicaciones en muchos servidores, y el archivo que guarda a cuáles puedes entrar.
- **MCP:** estándar para conectar a un agente con herramientas y servicios externos.
- **Nube:** computadoras y servicios que se alquilan por internet.
- **Perfil de shell:** archivo que la terminal ejecuta cada vez que se abre.
- **Plugin:** programa que amplía a otra herramienta.
- **Producción:** versión real y en uso de una aplicación, con datos de verdad.
- **Remoto (Git):** dirección del servidor donde se suben y bajan los cambios.
- **Repositorio:** carpeta de un proyecto junto con su historial de cambios.
- **Ruta UNC / unidad mapeada:** dirección de una carpeta en otra computadora de la red / letra que la representa.
- **Sandbox:** caja aislada que limita lo que un programa puede tocar.
- **SaaS:** servicio en internet que se usa sin instalarlo.
- **Skill:** carpeta con instrucciones y herramientas que enseñan al agente una tarea.
- **SQLite:** formato de base de datos contenida en un solo archivo.
- **SSH:** forma segura de conectarse a otra computadora o servicio con un par de claves.
- **Subagente:** agente auxiliar con su propio papel y permisos.
- **Symlink:** enlace simbólico; archivo o carpeta que en realidad muestra otra ubicación.
- **Terraform:** herramienta que crea infraestructura de nube a partir de archivos.
- **Token:** cadena larga que funciona como contraseña de un programa.
- **Transcripción:** registro completo de una sesión con el agente.
- **Variable de entorno:** ajuste con nombre que el sistema entrega a cada programa que arranca.
- **Versionado:** guardado en el historial de Git.
- **Volcado de memoria:** foto de lo que un programa tenía en memoria.
- **WSL2:** modo de Windows que ejecuta Linux dentro del sistema.
