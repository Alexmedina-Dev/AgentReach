# Catálogo de sugerencias de AgentReach / AgentReach suggestion catalog

Estado: borrador para revisión de Alex. Generado desde `catalogo-sugerencias.json` (misma información).

**Regla de oro:** AgentReach solo lee y nunca cambia archivos. Las sugerencias salen de este catálogo fijo, no de un modelo de lenguaje. Una regla de denegar o de pedir confirmación es **una política del agente, no una barrera del sistema operativo**. Los marcadores entre `< >` los cambia la persona por los suyos.

*Golden rule: AgentReach only reads and never changes files. Suggestions come from this fixed catalog, not from a language model. A deny or ask rule is an agent policy, not an operating system barrier. Placeholders between < > are replaced by the person with their own values.*

## 1. Tabla por tipo

| ID | Tipo (ES / EN) | Sugerencia (ES) | Suggestion (EN) | Regla a copiar | Cómo comprobar (ES) | How to check (EN) | Nivel máximo |
|---|---|---|---|---|---|---|---|
| TH-1 | Credencial en archivo del proyecto / *Credential stored in a project file* | Saca la credencial del proyecto, guardala en un gestor de secretos (un programa que guarda claves cifradas) y, si pudo quedar expuesta, cambiala por una nueva. | Move the credential out of the project into a secrets manager (a program that stores keys encrypted) and, if it may have been exposed, replace it with a new one. | R1, R2, R9, R10 | Vuelve a ejecutar AgentReach sobre la misma carpeta. El hallazgo TH-1 debe desaparecer o cambiar de sitio. | Run AgentReach again on the same folder. The TH-1 finding should disappear or move. | comprobado |
| TH-2 | Clave privada SSH / *Private SSH key* | No copies esa clave a la carpeta del proyecto. Protegela con frase de paso (una contrasena extra) y limita al agente en tu configuracion de usuario. | Do not copy that key into the project folder. Protect it with a passphrase (an extra password) and limit the agent in your user settings. | R3 | Vuelve a ejecutar AgentReach. Revisa en /permissions de Claude Code que la regla aparece. Para ver la huella de tus claves SSH, ssh-add -l es seguro: solo muestra huellas. | Run AgentReach again. In Claude Code, check that the rule appears in /permissions. To see your SSH key fingerprints, ssh-add -l is safe: it only shows fingerprints. | potencial |
| TH-3 | Credenciales de nube / *Cloud account credentials* | Usa credenciales temporales con solo los permisos que la tarea necesita y saca el archivo del alcance del agente. | Use temporary credentials with only the permissions the task needs, and keep the file out of the agent's reach. | R3 | Vuelve a ejecutar AgentReach. Confirma en /permissions que la regla aparece. | Run AgentReach again. Confirm the rule appears in /permissions. | potencial |
| TH-4 | Variable de entorno con secreto / *Environment variable holding a secret* | Quita esa variable del entorno con el que se lanza el agente y vuelve a abrir la terminal. | Remove that variable from the environment the agent starts with, then open a new terminal. | ninguna (no aplica) | Abre una terminal nueva sin la variable y vuelve a ejecutar AgentReach. Como AgentReach ve su propio entorno, el hallazgo puede seguir como hipotesis. | Open a new terminal without the variable and run AgentReach again. AgentReach sees its own environment only, so the finding may stay as a hypothesis. | hipotesis |
| TH-5 | Archivo de contexto con instrucciones sospechosas / *Context file with suspicious instructions* | Abre el archivo y borra las instrucciones que no escribiste tu. Si no sabes de donde vienen, no uses ese proyecto con el agente. | Open the file and remove instructions you did not write. If you do not know where they came from, do not use that project with the agent. | ninguna (no aplica) | Vuelve a ejecutar AgentReach; el texto sospechoso no debe aparecer. | Run AgentReach again; the suspicious text should no longer appear. | hipotesis |
| TH-6 | Enlace que sale del proyecto / *Link that leads out of the project* | Confirma que el enlace apunta a donde debe. Si no, borra solo el enlace, nunca la carpeta de destino. | Confirm the link points where it should. If not, delete only the link, never the destination folder. | ninguna (no aplica) | Vuelve a ejecutar AgentReach. El enlace debe desaparecer o mostrar el destino esperado. | Run AgentReach again. The link should disappear or show the expected destination. | potencial |
| TH-7 | Regla del agente demasiado permisiva / *Agent rule that is too permissive* | Cambia las reglas amplias de lectura, edicion, comandos y web a "pide confirmacion". Una confirmacion no es una barrera: solo hace que el agente pregunte. | Change broad read, edit, command and web rules to "ask first". A confirmation is not a barrier: it only makes the agent ask. | R7, R11, R12 | Vuelve a ejecutar AgentReach y revisa /permissions (Claude Code) o el archivo de configuracion (opencode). TH-7 debe bajar o desaparecer. | Run AgentReach again and check /permissions (Claude Code) or the configuration file (opencode). TH-7 should go down or disappear. | potencial |
| TH-8 | Capacidad de ejecutar programas (shell) / *Ability to run programs (shell)* | Limita los comandos permitidos o exige confirmacion antes de ejecutar comandos. Un shell (la linea de comandos) da acceso a lo que tu usuario puede tocar. | Restrict the allowed commands or require confirmation before running commands. A shell (the command line) reaches whatever your user account can touch. | R6, R11, R12 | Vuelve a ejecutar AgentReach y revisa las reglas de comandos en la configuracion de la plataforma. | Run AgentReach again and review the command rules in the platform configuration. | potencial |
| TH-9 | Script de despliegue / *Deployment script* | Revisa a mano que hace el script. Haz que el agente pida confirmacion antes de lanzarlo. | Review by hand what the script does. Make the agent ask before launching it. | R6 | Vuelve a ejecutar AgentReach. Revisa en /permissions que la regla aparece. | Run AgentReach again. Check in /permissions that the rule appears. | hipotesis |
| TH-10 | Plataforma sin sandbox / *Platform without a sandbox* | Ejecuta el agente en un entorno aislado, como una maquina virtual o un contenedor (una caja que aisla programas), si trabaja con carpetas importantes. | Run the agent in an isolated environment, such as a virtual machine or a container (a box that isolates programs), if it works with important folders. | ninguna (no aplica) | Revisa la version de tu plataforma (el reporte no la ve) y vuelve a ejecutar AgentReach. | Check your platform version (the report does not see it) and run AgentReach again. | potencial |
| TH-11 | Definicion de agente con herramientas / *Agent definition with tools* | Revisa las herramientas del archivo del agente y deja solo las necesarias para la tarea. | Review the tools in the agent's file and keep only those the task needs. | ninguna (no aplica) | Vuelve a ejecutar AgentReach tras editar la lista de herramientas. | Run AgentReach again after editing the tool list. | potencial |
| TH-12 | Texto invisible en instrucciones / *Invisible text in instructions* | Abre el archivo con un editor que muestre caracteres ocultos. Quita solo esos caracteres y lee el texto visible completo. | Open the file in an editor that shows hidden characters. Remove only those characters and read the full visible text. | ninguna (no aplica) | Vuelve a ejecutar AgentReach. TH-12 no debe aparecer. | Run AgentReach again. TH-12 should not appear. | comprobado |
| TH-13 | Instrucciones fuera de un proyecto / *Instructions outside a project* | Mueve el archivo a un proyecto que controles. Si ya no lo necesitas, borralo solo despues de confirmarlo. | Move the file into a project you control. If you no longer need it, delete it only after confirming. | ninguna (no aplica) | Vuelve a ejecutar AgentReach sobre la carpeta donde estaba. | Run AgentReach again on the folder where it was. | comprobado |
| TH-14 | Hook o servidor MCP que ejecuta un programa / *Hook or MCP server that runs a program* | Revisa el comando del hook (comando que la herramienta lanza sola) o del servidor MCP (conexion con herramientas externas). Desactiva el que no reconozcas y no aceptes la confianza de la carpeta hasta revisarlo. | Review the command of the hook (a command the tool launches by itself) or of the MCP server (a link to external tools). Disable any you do not recognize and do not accept folder trust until you have reviewed it. | R8 | Vuelve a ejecutar AgentReach. La entrada de hook o MCP debe desaparecer si la quitaste. | Run AgentReach again. The hook or MCP entry should disappear if you removed it. | potencial |
| TH-15 | Configuracion que salta los permisos / *Configuration that skips permissions* | Quita la opcion que salta los permisos y deja que el agente pida confirmacion. | Remove the option that skips permissions and let the agent ask for confirmation. | R5 | Vuelve a ejecutar AgentReach. En /permissions debe verse el modo normal. | Run AgentReach again. /permissions should show the normal mode. | potencial (en el proyecto); comprobado (en la configuracion del usuario) |
| TH-16 | Tarea que corre al abrir la carpeta / *Task that runs when the folder opens* | Borra la tarea de tasks.json o pon la opcion de tareas automaticas en "off" en los ajustes de VS Code. | Delete the task from tasks.json, or set the automatic tasks option to "off" in VS Code settings. | R13 | Vuelve a ejecutar AgentReach y abre la carpeta en VS Code para comprobar que no lanza tareas. | Run AgentReach again and open the folder in VS Code to check that no task starts. | potencial |
| TH-17 | Secreto de alto poder fuera de la tarea / *High-power secret outside the task* | Saca el secreto del proyecto, crea uno nuevo en la plataforma, desactiva el anterior y limita sus permisos. | Remove the secret from the project, create a new one on the platform, disable the old one and limit its permissions. | R1, R2 | Vuelve a ejecutar AgentReach. TH-17 debe desaparecer del archivo. | Run AgentReach again. TH-17 should disappear from the file. | potencial |
| TH-18 | Configuracion de git que ejecuta programas / *Git configuration that runs programs* | Revisa esas claves con git config --local --list, anota las que no reconozcas y quitalas solo tras confirmarlo. | Review those keys with git config --local --list, note the ones you do not recognize and remove them only after confirming. | R14 | Vuelve a ejecutar AgentReach. TH-18 debe bajar o desaparecer. | Run AgentReach again. TH-18 should go down or disappear. | comprobado (en algunos casos); potencial (en el resto) |
| TH-19 | Remoto de git con clave o direccion sospechosa / *Git remote with a key or a suspicious address* | Cambia la direccion del remoto para quitar la clave, y cambia esa clave por una nueva en el servicio. Despues usa un ayudante de credenciales. | Change the remote address to remove the key, and replace that key with a new one on the service. Then use a credential helper. | R15, R16 | Tras quitar la clave, vuelve a ejecutar AgentReach. Usa git remote -v solo despues del cambio, porque antes muestra la clave. | After removing the key, run AgentReach again. Use git remote -v only after the change, because before it shows the key. | comprobado (si la clave es literal); potencial (si es un token reconocido por prefijo o un valor de relleno) |
| TH-20 | Configuracion de git que no se pudo leer / *Git configuration that could not be read* | Revisa el archivo .git/config a mano y busca lineas raras, cortadas o repetidas. | Review the .git/config file by hand and look for odd, cut or repeated lines. | ninguna (no aplica) | Vuelve a ejecutar AgentReach tras corregir el archivo a mano. | Run AgentReach again after fixing the file by hand. | hipotesis |
| TH-21 | Memoria persistente de agentes instalada / *Persistent agent memory installed* | Este equipo guarda memoria de conversaciones en esta ruta; un agente con acceso de lectura a tu carpeta podria leerla. Si no la quieres, quita su entrada de configuracion. Si la usas, no hay nada que arreglar. | This computer keeps conversation memory at this path; an agent with read access to your folder could read it. If you do not want it, remove its configuration entry. If you use it, there is nothing to fix. | R4 | Si quitaste la entrada, vuelve a ejecutar AgentReach y comprueba que la senal ya no aparece. | If you removed the entry, run AgentReach again and check that the signal no longer appears. | comprobado (la entrada existe); potencial (su alcance) |
| TH-22 | Almacen local de conversaciones o memoria de agentes / *Local store of agent conversations or memory* | Revisa si quieres que el agente pueda leer ese historial. Si no, pon una regla de lectura denegada en tu configuracion de usuario, usando la ruta que hayas confirmado. | Check whether you want the agent to be able to read that history. If not, add a read deny rule in your user settings, using the path you have confirmed. | R4 | Vuelve a ejecutar AgentReach y revisa /permissions. | Run AgentReach again and check /permissions. | potencial |

## 2. Reglas a copiar, con fuente y estado

Cada regla dice dónde va, el valor exacto, la fuente (ver sección 4) y si está verificada. Lo que no se confirmó dice **no verificado**.

### R1: Claude Code, archivos del proyecto

- **Dónde:** <proyecto>/.claude/settings.json, bloque permissions.deny
- **Valor:** `"deny": ["Read(./.env)", "Read(./.env.*)"]`
- **Fuente:** F1 (formato Read(./ruta) confirmado; el comodin .env.* usa la misma sintaxis gitignore, no hay ejemplo literal con .env.*)
- **Estado:** parcialmente verificado
- **Nota (ES):** Impide que las herramientas de lectura, edicion y escritura de Claude Code toquen esos archivos. Es una regla de Claude Code, no una barrera del sistema operativo. No se sabe si un comando de Bash los lee igual: no verificado.
- **Note (EN):** Stops Claude Code's read, edit and write tools from touching those files. It is a Claude Code rule, not an operating system barrier. Whether a Bash command can still read them is not verified.

### R2: Claude Code, un archivo concreto

- **Dónde:** <proyecto>/.claude/settings.json, bloque permissions.deny
- **Valor:** `"deny": ["Read(./<nombre-del-archivo>)"]`
- **Fuente:** F1
- **Estado:** verificado (formato)
- **Nota (ES):** Mismo efecto que R1 para un solo archivo. En Windows las rutas se escriben con barra normal.
- **Note (EN):** Same effect as R1 for one file. On Windows, write paths with forward slashes.

### R3: Claude Code, carpeta personal (aplica a todos los proyectos)

- **Dónde:** ~/.claude/settings.json, bloque permissions.deny
- **Valor:** `"deny": ["Read(~/.ssh/**)", "Read(~/.aws/**)"]`
- **Fuente:** F1 (prefijo ~/ y reglas de ajustes de usuario: confirmados)
- **Estado:** verificado (formato); la ruta exacta de la carpeta depende del equipo
- **Nota (ES):** Aplica a todas las carpetas. Solo cambia lo que Claude Code puede leer; no es una barrera del sistema.
- **Note (EN):** Applies to every folder. It only changes what Claude Code can read; it is not a system barrier.

### R4: Claude Code, carpeta de memoria o historial (marcador)

- **Dónde:** ~/.claude/settings.json, bloque permissions.deny
- **Valor:** `"deny": ["Read(~/<carpeta-de-memoria>/**)"]`
- **Fuente:** F1 (formato). La ruta de la carpeta no esta verificada (TH-22).
- **Estado:** no verificado (ruta por verificar)
- **Nota (ES):** Usa solo la ruta que la persona confirme en su equipo.
- **Note (EN):** Use only the path the person confirms on their machine.

### R5: Claude Code, saltar permisos

- **Dónde:** <proyecto>/.claude/settings.json o ~/.claude/settings.json
- **Valor:** `"permissions": { "disableBypassPermissionsMode": "disable" }  (y quitar "defaultMode": "bypassPermissions" si existe)`
- **Fuente:** F1 (clave y valor confirmados)
- **Estado:** verificado
- **Nota (ES):** Impide que el modo de saltar permisos se use. Quitar la opcion de salto es decision de la persona.
- **Note (EN):** Prevents the skip-permissions mode from being used. Removing the skip option is the person's decision.

### R6: Claude Code, comandos de Bash que deben pedir confirmacion

- **Dónde:** <proyecto>/.claude/settings.json, bloque permissions.ask
- **Valor:** `"ask": ["Bash(./<script-de-despliegue> *)"]`
- **Fuente:** F1 (orden deny, ask, allow confirmado; las reglas Bash solo cubren la forma escrita del comando)
- **Estado:** verificado (formato); sin frontera de seguridad
- **Nota (ES):** Solo cubre la forma exacta que se escribe. Otra forma de llamar al mismo programa puede no coincidir. No es una barrera.
- **Note (EN):** Only covers the exact form written. Another way of calling the same program may not match. Not a barrier.

### R7: Claude Code, pedir confirmacion para todos los comandos

- **Dónde:** <proyecto>/.claude/settings.json, bloque permissions.ask
- **Valor:** `"ask": ["Bash"]`
- **Fuente:** no verificado: la forma sin patron no aparece en la documentacion leida; comprobarla con /permissions tras guardar
- **Estado:** no verificado
- **Nota (ES):** Si /permissions no muestra la regla, no se aplico: no darla por buena.
- **Note (EN):** If /permissions does not show the rule, it was not applied: do not assume it works.

### R8: Claude Code, servidor MCP

- **Dónde:** <proyecto>/.claude/settings.json, bloque permissions.deny
- **Valor:** `"deny": ["mcp__<servidor>__*"]`
- **Fuente:** F1 (forma mcp__servidor__* confirmada en el texto de reglas de MCP)
- **Estado:** verificado (formato)
- **Nota (ES):** Desactiva las herramientas de ese servidor. Es una regla de Claude Code, no una barrera.
- **Note (EN):** Disables that server's tools. It is a Claude Code rule, not a barrier.

### R9: opencode 1.x, lectura de .env

- **Dónde:** <proyecto>/opencode.json o .opencode/opencode.json
- **Valor:** `"permission": { "read": { "*.env": "deny", "*.env.*": "deny", "*.env.example": "allow" } }`
- **Fuente:** F2 (forma de objeto por herramienta con patrones confirmada con bash; read con deny no visto literal)
- **Estado:** parcialmente verificado
- **Nota (ES):** La ultima regla que coincide gana: *.env.example va al final para quedar permitido. Es una politica del agente, NO una barrera del sistema: el documento no dice que proteja frente a comandos de shell (bash en 1.x). Un comando de shell puede leer el archivo igualmente.
- **Note (EN):** The last matching rule wins: *.env.example goes last so it stays allowed. It is an agent policy, NOT a system barrier: the docs do not say it protects against shell commands (bash in 1.x). A shell command may still read the file.

### R10: opencode 2.x, lectura de .env

- **Dónde:** <proyecto>/opencode.json, clave permissions (lista)
- **Valor:** `"permissions": [ {"action": "read", "resource": "*.env", "effect": "deny"}, {"action": "read", "resource": "*.env.*", "effect": "deny"}, {"action": "read", "resource": "*.env.example", "effect": "allow"} ]`
- **Fuente:** F3 (forma {action, resource, effect} y ultima regla gana confirmadas; el valor deny es el mismo campo que ask/allow)
- **Estado:** parcialmente verificado
- **Nota (ES):** Politica del agente, no barrera. En 2.x la accion shell corre con la autoridad del usuario: un deny de read no la frena (no afirmado por la documentacion; tratar como no protegido).
- **Note (EN):** Agent policy, not a barrier. In 2.x the shell action runs with the user's authority: a read deny does not stop it (the docs do not say it does; treat it as not protected).

### R11: opencode 1.x, pedir confirmacion para comandos de shell

- **Dónde:** <proyecto>/opencode.json, clave permission
- **Valor:** `"permission": { "bash": "ask" }`
- **Fuente:** F2 y F4 (ejemplo de la guia 1.x)
- **Estado:** verificado (formato)
- **Nota (ES):** Pide confirmacion antes de cada comando. No es una barrera.
- **Note (EN):** Asks before each command. Not a barrier.

### R12: opencode 2.x, pedir confirmacion para shell

- **Dónde:** <proyecto>/opencode.json, clave permissions (lista)
- **Valor:** `"permissions": [ {"action": "shell", "resource": "*", "effect": "ask"} ]`
- **Fuente:** F3 (accion shell y forma de lista confirmadas)
- **Estado:** verificado (formato)
- **Nota (ES):** Pide confirmacion antes de cada comando. No es una barrera.
- **Note (EN):** Asks before each command. Not a barrier.

### R13: VS Code, tareas que se lanzan al abrir la carpeta

- **Dónde:** Ajustes de VS Code (settings.json del usuario)
- **Valor:** `"task.allowAutomaticTasks": "off"`
- **Fuente:** F5 (fuente primaria segun el PRD, verificada el 2026-11-09; no releida hoy)
- **Estado:** verificado en el PRD; no releido hoy
- **Nota (ES):** Desactiva las tareas automaticas en todas las carpetas.
- **Note (EN):** Turns off automatic tasks in every folder.

### R14: git, revisar claves de programas

- **Dónde:** Terminal, dentro del proyecto (solo lectura)
- **Valor:** `git config --local --list`
- **Fuente:** F5 (clave y riesgo por TH-18; no releido hoy en la documentacion de git)
- **Estado:** verificado en el PRD; no releido hoy
- **Nota (ES):** Solo lista la configuracion. Si aparece una direccion con clave dentro, no la copies a ningun sitio.
- **Note (EN):** Only lists the configuration. If an address with a key appears, do not copy it anywhere.

### R15: git, quitar la clave de una direccion de remoto

- **Dónde:** Terminal, dentro del proyecto
- **Valor:** `git remote set-url origin <direccion-sin-clave>`
- **Fuente:** F5 (no releido hoy)
- **Estado:** no verificado hoy
- **Nota (ES):** Cambia la direccion. Hazlo solo tras confirmar con la persona; cambia tambien la clave en el servicio.
- **Note (EN):** Changes the address. Do it only after the person confirms; also change the key on the service.

### R16: git, ayudante de credenciales

- **Dónde:** Terminal, configuracion de usuario
- **Valor:** `git config --global credential.helper <ayudante-elegido>`
- **Fuente:** F5 (el PRD menciona un fallo de wincred; el nombre del ayudante recomendado no esta verificado)
- **Estado:** no verificado
- **Nota (ES):** No se sabe que ayudante recomendar hoy. Consultar la documentacion oficial de git antes de cambiarlo.
- **Note (EN):** The recommended helper is not known for certain today. Check the official git documentation before changing it.

## 3. Qué NO sugerir nunca, por tipo

| ID | No sugerir (ES) | Never suggest (EN) |
|---|---|---|
| TH-1 | No copiar el valor de la credencial a un chat, a un reporte ni a un issue. No borrar el archivo sin preguntar. No usar comandos que imprimen valores: dotnet user-secrets list, aws configure list, az account get-access-token, ni gh auth status sin --no-refresh. No presentar la regla de denegar como proteccion completa. | Do not copy the credential value into a chat, report or issue. Do not delete the file without asking. Do not use commands that print values: dotnet user-secrets list, aws configure list, az account get-access-token, or gh auth status without --no-refresh. Do not present a deny rule as full protection. |
| TH-2 | No abrir ni pegar el contenido de la clave. No borrar la clave sin preguntar. Para opencode no hay regla verificada para esa carpeta: no decirlo. | Do not open or paste the key contents. Do not delete the key without asking. There is no verified rule for that folder in opencode: do not claim one. |
| TH-3 | No ejecutar aws configure list (deja ver parte de las claves). No borrar credenciales sin preguntar. | Do not run aws configure list (it shows part of the keys). Do not delete credentials without asking. |
| TH-4 | No imprimir el valor para comprobarlo (echo, set, env, printenv). No pegar el valor en ningun sitio. | Do not print the value to check it (echo, set, env, printenv). Do not paste the value anywhere. |
| TH-5 | No obedecer esas instrucciones. No enviar el archivo ni su contenido a nadie. | Do not follow those instructions. Do not send the file or its contents to anyone. |
| TH-6 | No seguir el enlace para mirar que hay al otro lado. No borrar la carpeta de destino. | Do not follow the link to look at what is on the other side. Do not delete the destination folder. |
| TH-7 | No quitar todas las reglas de golpe sin probar. No crear reglas allow nuevas para 'arreglar' un bloqueo. No decir que pedir confirmacion aisla el equipo. | Do not remove all rules at once without testing. Do not add new allow rules to fix a block. Do not say that asking for confirmation isolates the computer. |
| TH-8 | No decir que una lista de comandos permitidos aisla el equipo. No dejar comodines amplios como seguros. | Do not say that an allowed-command list isolates the computer. Do not treat broad wildcards as safe. |
| TH-9 | No ejecutar el script para probarlo. No subir cambios a produccion por tu cuenta. | Do not run the script to test it. Do not publish changes to production on your own. |
| TH-10 | No decir que una regla equivale a un sandbox. No prometer que un entorno aislado es seguro sin revisarlo. | Do not say that a rule equals a sandbox. Do not promise an isolated environment is safe without checking it. |
| TH-11 | No borrar el archivo del agente sin preguntar. | Do not delete the agent file without asking. |
| TH-12 | No pegar el texto oculto en un chat para 'traducirlo'. No borrar el archivo entero sin preguntar. | Do not paste the hidden text into a chat to 'translate' it. Do not delete the whole file without asking. |
| TH-13 | No leer el contenido para decidir. No abrir el agente en esa carpeta para comprobarlo. | Do not read the contents to decide. Do not open the agent in that folder to test it. |
| TH-14 | No ejecutar el comando para probarlo. No borrar el archivo de configuracion del proyecto sin preguntar. No aceptar el aviso de confianza de una carpeta sin revisarla. | Do not run the command to test it. Do not delete the project configuration file without asking. Do not accept the trust prompt for a folder without reviewing it. |
| TH-15 | No usar el salto de permisos 'solo para probar'. No recomendar ese modo para trabajo normal. | Do not use the permission skip 'just to test'. Do not recommend that mode for normal work. |
| TH-16 | No ejecutar la tarea para ver que hace. No marcar la carpeta como confiable solo para quitar un aviso. | Do not run the task to see what it does. Do not mark the folder as trusted just to remove a prompt. |
| TH-17 | No pegar el token en ningun sitio. No usar el token para comprobar si funciona. No revocar otros tokens sin preguntar. | Do not paste the token anywhere. Do not use the token to check whether it works. Do not revoke other tokens without asking. |
| TH-18 | No ejecutar git log, git show ni git status mientras revisas la configuracion: algunas claves lanzan programas al usarse. No copiar direcciones con clave que aparezcan en la lista. | Do not run git log, git show or git status while reviewing the configuration: some keys launch programs when used. Do not copy any address containing a key that shows up in the list. |
| TH-19 | No copiar la direccion con la clave a un chat o a un issue. No cambiar la direccion sin confirmar antes con la persona. | Do not copy the address with the key into a chat or issue. Do not change the address without confirming with the person first. |
| TH-20 | No ejecutar git para 'arreglarlo'. No borrar el archivo sin preguntar. | Do not run git to 'fix' it. Do not delete the file without asking. |
| TH-21 | No abrir, copiar ni borrar la base de datos de memoria sin preguntar. No calificar la memoria como mala o insegura. | Do not open, copy or delete the memory database without asking. Do not describe the memory as bad or unsafe. |
| TH-22 | No inventar la ruta del almacen. No leer el contenido del historial. No borrar historial sin preguntar. | Do not invent the store's path. Do not read the history contents. Do not delete history without asking. |

## 4. Fuentes oficiales y estado de verificación

- **F1 Permisos de Claude Code (reglas Read, Edit, Bash; orden deny, ask, allow)** — https://code.claude.com/docs/en/permissions (leída 2026-11-10 (WebFetch, resumen y texto de la pagina)). Confirma: Formato de regla Read(./.env); prefijos ./, // (raiz absoluta), ~/ (carpeta personal); en Windows las rutas se normalizan a /c/...; Read(path) bloquea las herramientas de lectura y tambien Edit y Write sobre la misma ruta; orden de evaluacion deny, luego ask, luego allow; la clave permissions.disableBypassPermissionsMode con valor disable; las reglas de Bash no son frontera de seguridad y el documento remite a sandboxing para imponer limites. No confirma: Si una regla Read deny impide que un comando de Bash (por ejemplo cat) lea el archivo: el documento no lo afirma.
- **F2 Permisos de opencode 1.x (clave permission, objeto por herramienta)** — https://opencode.ai/v1/docs/permissions (redirigida desde https://docs.opencode.ai/docs/permissions) (leída 2026-11-10 (WebFetch, resumen)). Confirma: Clave permission con objeto por herramienta, ejemplo {"bash": {"*": "ask", "git *": "allow"}}; comodines * y ?; los .env requieren aprobacion por defecto (*.env y *.env.* en ask, *.env.example en allow); la ultima regla que coincide gana. No confirma: Que una regla de read o edit en deny proteja frente a comandos de shell: el documento no lo dice. Forma exacta de read con deny: no vista literal (deducida de la forma de bash).
- **F3 Permisos de opencode 2.x (lista permissions con action, resource, effect)** — https://opencode.ai/docs/permissions (leída 2026-11-10 (WebFetch, resumen)). Confirma: Lista de reglas {action, resource, effect}; accion shell para comandos; comodines; los .env por defecto en ask y *.env.example en allow; la ultima regla que coincide gana; shell corre con la autoridad del usuario del equipo. No confirma: Que un deny de read proteja frente a shell: no se afirma; el documento no llama a los permisos sandbox.
- **F4 Investigacion previa de opencode 1.x frente a 2.x** — _bmad-output/planning-artifacts/research/opencode-1x-frente-a-2x.md (leída 2026-11-10 (lectura local)). Confirma: Regla de trabajo: un deny de read o edit NO protege frente al shell (politica, no barrera); external_directory pasa de ask (1.x) a allow (2.x); clave bash=shell en 2.x; carpeta de politicas de organizacion solo en 2.x (solo niega).
- **F5 PRD de AgentReach (catalogo TH-1 a TH-22, FR-5, FR-6, FR-7, FR-11, FR-12)** — _bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md (leída 2026-11-10 (lectura local)). Confirma: Niveles maximos por tipo; regla de nivel para deny y ask; comandos que NO deben sugerirse (FR-10); clave de VS Code task.allowAutomaticTasks con valor off (fuente primaria segun el PRD, no releida hoy).
- **F6 Codigo de tipos y textos actuales** — src/agentreach/contracts/finding.py (leída 2026-11-10 (lectura local)). Confirma: Tipos TH-1 a TH-20 y textos actuales de que hacer y que significa. TH-21 y TH-22 existen solo en el PRD (no en el codigo todavia).

## 5. Lo que quedó sin verificar

- Si una regla `Read` de Claude Code en deny impide que un comando de Bash lea el archivo (la documentación leída no lo afirma).
- La forma exacta de `read` con `deny` en opencode 1.x (se dedujo de la forma de `bash`, no se vio literal) y el valor `deny` en 2.x.
- Que `ask` sin patrón (`"ask": ["Bash"]`) funcione en Claude Code (R7).
- Rutas de Windows de opencode (global, `auth.json`) y la clave `share`.
- Que Claude Code en Windows nativo no tenga sandbox y la versión mínima que lo cambiaría (dato del PRD, no releído hoy).
- La clave de VS Code `task.allowAutomaticTasks` (R13), la forma de quitar la clave de un remoto (R15) y el nombre del ayudante de credenciales recomendado (R16).
- Políticas de organización en opencode 2.x (clave `experimental.policies`): dato de la investigación previa, no releído hoy.
- Ruta exacta de las carpetas de memoria y de historial (TH-21, TH-22): por verificar.

Para cada punto sin verificar, la sugerencia no promete el resultado; el texto lo dice (regla 'no verificado').
