---
title: 'Historia 16. Detector de caracteres Unicode invisibles'
type: 'feature'
created: '2026-11-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['{project-root}/_bmad-output/planning-artifacts/historias-mvp.md']
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problema:** un archivo de instrucciones puede llevar caracteres que no se dibujan pero que un agente lee (etiquetas U+E0000, ancho cero, cambio de dirección...), escondiendo una orden que la persona no ve.

**Enfoque:** `DetectorInvisibles` revisa los archivos de instrucciones del proyecto con la lectura segura y reporta TH-12 con ruta y línea, contando por grupo cuántos hay, sin decodificar ni copiar nunca el mensaje.

## Boundaries & Constraints

**Always:** el mensaje oculto nunca sale; un archivo que no se pueda leer sale como `NoRevisado`, no como "sin invisibles"; los caracteres de la prueba se generan con `chr(...)`; la BOM del inicio no cuenta; no se reportan emoji compuestos, selectores pegados a un emoji ni banderas.

**Never:** el nivel (Historia 11); extensiones de editor ni carpeta personal; instrucciones en lenguaje natural sin trucos de formato.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| AT-01 | etiquetas U+E0000 en `.cursor/rules/estilo.mdc` | TH-12 con su línea | — |
| AT-09 | U+200B suelto en copilot-instructions | TH-12 con su línea | — |
| AT-02 / CX-01 | emoji compuesto y bandera / CLAUDE.md limpio | nada | — |
| BOM al inicio | `BOM + texto` | nada | — |
| No UTF-8, binario, 5 MB+1, enlace, tubería | archivo ilegible | `NoRevisado` con su motivo | sin decodificar a la fuerza |

</intent-contract>

## Code Map

- `src/agentreach/collectors/invisibles.py` -- `DetectorInvisibles`, `contar_invisibles`, `es_archivo_de_instrucciones`.
- `src/agentreach/app/auditar.py` -- registro (una línea).
- Proyecto de prueba: `proyecto/.cursor/rules/estilo.mdc` (AT-01), `docs/emoji.md` (AT-02), `.github/copilot-instructions.md` (AT-09), `CLAUDE.md` (CX-01).

## Tasks & Acceptance

**Execution:**
- `tests/test_invisibles.py` -- primero
- `collectors/invisibles.py` y el registro

**Acceptance Criteria:**
- Given (a)-(d) de la historia, when se ejecutan, then se cumplen y AT-01 y AT-09 se detectan; AT-02 y CX-01 no.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~26 findings (ciega 11, casos limite 12 mas 3 de afirmaciones) - high 2, medium 7, low 4, false 0, maybe-false 0
- `[high]` `[patch]` una "bandera" con etiquetas largas (bandera negra + mensaje + cierre) se aceptaba como legitima y escondia un mensaje entero - ahora solo las tres banderas que existen (gbeng, gbsct, gbwls); cualquier otro contenido se reporta
- `[high]` `[patch]` el analisis de tramos de etiquetas era cuadratico (un tramo de 200 000 caracteres paraba la auditoria) - el tramo se evalua una vez
- `[medium]` `[patch]` la linea se truncaba a 200 000 caracteres en silencio y lo de despues parecia limpio - ya no se trunca
- `[medium]` `[patch]` rangos que faltaban: selectores de variacion suplementarios U+E0100 a E01EF, aislamientos bidi U+2066 a 2069 y U+061C, formatos obsoletos U+206A a 206F
- `[medium]` `[patch]` cualquier simbolo contaba como emoji junto a un ZWJ (se podian intercalar invisibles entre cajas y flechas) - solo pictogramas y una lista explicita; tope de 24 invisibles "legitimos" por linea; U+203C y U+2139 con FE0F siguen siendo legitimos
- `[medium]` `[patch]` un archivo de instrucciones que es enlace o junction no se seguia ni se informaba (parecia limpio) - sale como NoRevisado (no_es_archivo_regular)
- `[low]` `[patch]` lista de archivos ampliada (.clinerules, .roorules, CONVENTIONS.md, .github/prompts, .windsurf/rules, README en cualquier carpeta, sin .venv ni venv ni site-packages); `..cfg/` ya no se confunde con "fuera del proyecto"; ValueError al leer; comentario del nivel
- `[low]` `[defer]` texto legitimo en persa, arabe, hebreo e indicas se reporta (ZWNJ, LRM, RLM): sin lista por escritura es preferible el aviso de mas - documentado en el modulo
- `[low]` `[defer]` otros invisibles (U+00AD, U+034F, rellenos de Hangul, U+2800), JSON de configuracion de agentes y las pruebas del proyecto de prueba que se omiten sin la variable
- `[reject]` detalles/no_revisados no llegan al reporte aun (Historia 13), nivel provisional (Historia 11), prueba de tamano con numeros magicos

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorInvisibles` (TH-12) sobre archivos de instrucciones, con seis grupos de rangos (etiquetas, ancho cero, direccion, operadores, selectores de variacion, BOM intermedio), exclusiones de emoji compuestos, teclas y las tres banderas con etiquetas, y conteo por linea y grupo sin copiar nunca el mensaje.
Archivos: `collectors/invisibles.py`, `app/auditar.py` (una linea), `tests/test_invisibles.py`, `tests/test_primera_ejecucion.py`.
Verificacion: con el proyecto de prueba 488 pasan, 13 omitidas; sin el 459 pasan, 42 omitidas. Ruff limpio. AT-01 (estilo.mdc:5) y AT-09 (copilot-instructions.md:3) se detectan; AT-02 y CX-01 no.
Sin commit. Riesgo residual: los `defer`.
