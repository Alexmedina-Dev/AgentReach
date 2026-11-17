# Validation Report — PRD AgentReach (v0.2)

- **PRD:** `_bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md`
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-11-11
- **Grade:** Fair (2 hallazgos altos; ninguna dimensión débil ni rota)
- **Foco pedido:** la nota de Fase 2 sobre `hooks.PreToolUse` (§7.2) y la decisión de la pregunta 9 (`--redact-paths` apagada por defecto)

## Overall verdict

El PRD tiene una tesis clara y honesta, contramétricas reales (SM-C1 a SM-C3) y un alcance muy explícito, con trazabilidad de decisiones poco común. El riesgo está en la última capa de cambios: las decisiones del 2026-11-11 se anotaron donde cabían en vez de reconciliarse con los FR existentes. FR-5, FR-7 y FR-17 todavía describen niveles anteriores a la Historia 27, y `--redact-paths` es una decisión sin FR ni criterios comprobables.

**Sobre los dos cambios pedidos:** ninguno contradice FR-3, FR-17, FR-27, §7.3 ni §9, pero tampoco están conectados con ellos. La nota de `hooks.PreToolUse` carece de condición de entrada, y la decisión de la pregunta 9 no registra lo que se cede.

## Dimension verdicts

- Decision-readiness — adecuado
- Substance over theater — fuerte
- Strategic coherence — fuerte
- Done-ness clarity — adecuado
- Scope honesty — fuerte
- Downstream usability — adecuado
- Shape fit — adecuado

## Findings by severity

### Critical (0)

### High (2)

**[Downstream usability]** — FR-5, FR-7 y FR-17 siguen con los niveles previos a la Historia 27 (FR-5 tabla y ejemplo `.env.staging`; FR-7; FR-17 «PP-01 … comprobado en opencode»; FR-18/FR-23 «nivel máximo del tipo»)
Quien escriba historias o pruebas desde los FR usará el ejemplo de «comprobado» de FR-5 como caso de prueba, y está invertido. §7.3 ya lo admite («Pendiente de reconciliar»), pero eso no sustituye corregir el FR.
Fix: editar los cuatro lugares (ejemplo de FR-5 o tope explícito en la tabla; FR-7; FR-17 con «ver SM-7» o cifras vigentes) y retirar el párrafo «Pendiente de reconciliar» de §7.3.

**[Done-ness clarity]** — `--redact-paths` sin FR ni consecuencias comprobables (§10 pregunta 9; FR-27; FR-3; §7.3)
Es requisito previo al lanzamiento público pero vive solo en una respuesta de §10 y en la Story 7.6. Sin definir: qué se redacta, en qué formatos (terminal, HTML, JSON y CSV exportados, `--salida`), cómo convive con la «ruta real» del permiso (FR-30) y con el comando de verificación de FR-10 (que necesita la ruta real), y si el reporte declara que se redactó. No está en la lista «Antes del lanzamiento público» de §7.3.
Fix: crear **FR-33** con tres consecuencias comprobables (el reporte «para compartir» no contiene la carpeta personal ni el usuario; aviso de que la verificación exacta requiere la ruta real; el modo queda declarado en el reporte) y sumarlo a §7.3.

### Medium (8)

**[Decision-readiness]** — Pregunta 9 con estado contradictorio y costo no registrado (§10)
Sigue rotulada «Abierta de verdad» y contiene una decisión. No dice qué se cede con «apagada por defecto»: el HTML con rutas queda guardado en `AgentReach-reportes` en cada revisión.
Fix: rotularla «DECIDIDA, pendiente de construir», anotar el costo asumido y la condición que la reabriría.

**[Strategic coherence]** — Nota de Fase 2 sobre `hooks.PreToolUse` sin condición de entrada y con cifras sin reconciliar (§7.2)
Dice «4 hallazgos» mientras SM-8 y FR-32 hablan de «17» (son corridas distintas, pero no se dice). «No es un defecto» choca en tono con §9 y SM-8. Remite a «AD-11», que el PRD no define, y no aclara que TH-14 y TH-21 sí leen `hooks` en el MVP.
Fix: condición de entrada («solo con fuente verificada del efecto del hook y tras medir SM-8»), nombrar las dos corridas, aclarar TH-14 y TH-21 y reemplazar «AD-11» por «tope por nombre (FR-1, punto 5)».

**[Scope honesty]** — Texto que sigue diciendo «pendiente» (FR-3 línea ~103; §9)
FR-3 remite a la pregunta 9 como abierta, y §9 cita como mitigación una opción que todavía no existe.
Fix: FR-3 a «apagada por defecto, modo para compartir (FR-33)»; §9 a «aún no construida; requisito previo al lanzamiento público», admitiendo el riesgo residual.

**[Scope honesty]** — FR-31 no cubre «agente analizado sin señales de configuración» (FR-31; FR-29; FR-17; FR-20)
Nada impide leer «analizado, sin hallazgos» como «sin exposición», que es la falsa cobertura que FR-31 combate. **Sí conviene una regla.**
Fix: cuarta clase en FR-31, «analizado, sin señales de configuración», con tres consecuencias: (a) nunca se muestra como «sin hallazgos» a secas; (b) sus hallazgos no pasan de potencial salvo que los valores por defecto de la plataforma tengan fuente verificada; (c) el reporte dice qué archivos buscó y no encontró. **Confirmar (b) con la verificación de la historia 40** antes de fijarlo.

**[Done-ness clarity]** — FR sin consecuencias comprobables o con criterio subjetivo (FR-8, FR-14, FR-16, FR-28, FR-29; FR-11 «un novato puede entender»)
Fix: una o dos consecuencias comprobables por FR, o remitir a los casos del oráculo que ya las cubren.

**[Done-ness clarity]** — FR-14 contradice la lista de FR-32 (`sandbox` y `permissions.*` figuran como no interpretados)
Fix: precisar en FR-32 qué forma queda sin modelar, y en FR-14 añadir «salvo las formas listadas en FR-32».

**[Downstream usability]** — La regla «tope por nombre» vive en FR-1, punto 5, y solapa con «Alcance de FR-7»
Es una regla de nivel de confianza, y no está en el máximo por tipo de FR-18 (TH-1, TH-17).
Fix: moverla a FR-5 o FR-7, dejar un puntero en FR-1 y unificar.

**[Downstream usability]** — FR-27 no cubre las rutas fuera de la carpeta revisada (TH-2, TH-3, TH-13, destino de TH-6, `~/.claude/settings.json`)
Fix: una frase en FR-27 («fuera de la carpeta revisada, `~/…` o la ruta absoluta según `--redact-paths`») y una nota en FR-10.

### Low (4)

- **[Decision-readiness]** Preguntas con forma de tarea y numeración desordenada (§10: 1, 10, 21 antes de la 20, 28 y 22 al final). Fix: reordenar y convertir 1 y 10 en tareas.
- **[Downstream usability]** Referencias a IDs que el PRD no define (`AD-11`, «Story 7.6», «M1»). Fix: línea de mapa en §0 y usar «Historia» en todo el documento.
- **[Downstream usability]** Índice de supuestos con deriva (§11: consulta del color de FR-27; FR-22). Fix: alinear ambas direcciones.
- **[Shape fit]** Historial dentro del texto normativo (§7.3 punto 2, SM-7 «Antes eran 18…», FR-1 «Precisión de la Historia 21»). Fix: dejar solo el recuento vigente y mover el histórico al `.memlog.md`.

## Mechanical notes

- IDs contiguos y únicos: FR-1 a FR-32, TH-1 a TH-22, SM-1 a SM-8 (con SM-C1 a C3); preguntas 1 a 31 completas pero impresas en desorden.
- Cruces: FR-3 (línea ~103) → pregunta 9 resuelve pero está desfasada; FR-27 ↔ pregunta 9 coherentes; FR-17 → §7.3 diverge en la lista de casos comprobados.
- Glosario: falta definir «modo para compartir»; «configurado, reconocido y analizado» son candidatos a glosario.
- Ninguna historia de usuario (UJ) cubre el flujo de «compartir» el reporte, que es el que justifica `--redact-paths`.

## Reviewer files

- `review-rubric.md` (revisión completa por dimensión)
- No se corrió revisor adversarial adicional.
