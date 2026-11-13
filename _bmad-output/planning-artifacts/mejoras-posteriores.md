# Mejoras posteriores (después de cerrar el 100 % del MVP)

Lista de mejoras acordadas con Alex que NO bloquean el MVP. Se retoman cuando el proyecto esté terminado y probado.

## M1. Que un agente no pueda "escribir la S" por la persona

> **Actualización 2026-11-11 (Alex, vía el análisis de John):** M1 deja de ser "posterior" y pasa a **requisito previo al lanzamiento público** (PRD, FR-30). No bloquea el MVP en pruebas. Mínimo exigido: las ideas 1 (leer `CONIN$` o `/dev/tty`) y 5 (registrar el modo de ejecución en el reporte); las 2, 3 y 4 son refuerzos a evaluar. Criterio de terminado: la prueba descrita abajo (tubería, pseudoterminal y variable de entorno de un agente).

**Origen (2026-11-10).** AgentReach pide permiso de lectura con una pregunta (S/N) y no existe `--permitir`. Pero un agente decidido
podría simular una terminal interactiva (un pseudoterminal) y escribir la `s` por la persona. Hoy AgentReach no puede impedirlo
técnicamente. Lo que sí hace: el reporte declara su alcance y sus límites, nunca dice "seguro", y la guía dice que la revisión válida
es la que ejecuta la persona. **Alex: "es verdad, pero también lo podemos evitar, solo hay que hacerlo bien".**

**Objetivo.** Que la autorización solo pueda darla una persona presente, con defensa en capas y sin prometer lo que no se pueda
garantizar.

**Ideas a investigar y probar (ninguna verificada todavía):**
1. Leer la confirmación del dispositivo de consola real (en Windows `CONIN$`, en Linux y macOS `/dev/tty`) y no de la entrada estándar.
2. Detectar que el proceso padre o el entorno son de un agente de IA (nombres de proceso, variables de entorno propias de cada agente) y
   rechazar con un mensaje claro. Es una heurística: hay que decir que no es infalible.
3. Una confirmación que requiera un gesto humano fuera de la terminal (un cuadro de diálogo del sistema), si el sistema lo permite.
4. Un reto-respuesta (un código mostrado en pantalla que hay que reescribir): ayuda contra el Enter automático, no contra un agente que
   lea la pantalla.
5. Registrar en el reporte el modo de ejecución (interactivo real o no determinado) para que quien lo lea sepa con qué confianza se hizo.

**Criterio de terminado (a definir):** una prueba que simule un agente ejecutando AgentReach por una tubería, por un pseudoterminal y
con la variable de entorno de un agente conocido, y compruebe que en los tres casos no lee la carpeta o lo declara. Documentar con
honestidad lo que sigue sin poder impedirse.

**Depende de:** MVP al 100 %, y la decisión de qué defensas se pueden verificar en Windows, Linux y macOS.
