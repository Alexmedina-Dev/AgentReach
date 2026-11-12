"""Mide el contraste del reporte HTML sobre PÍXELES REALES (no sobre colores declarados).

Método: se abre el reporte en un navegador, se listan los textos visibles y los controles con borde, se vuelve a pintar la página
con el texto transparente (así queda solo el fondo real: degradados, cristal, líneas decorativas) y se mide, píxel por píxel dentro
de la caja de cada texto, la razón de contraste entre el color del texto y ese fondo. El resultado es el PEOR píxel (el primer
percentil se usa solo para ignorar el borde antialiasado de la caja). Mínimos: 4,5 para texto normal; 3 para texto grande
(24 px, o 18,66 px en negrita) y para el borde de los controles.

Necesita ``playwright`` y un navegador (Edge o Chromium); las pruebas se omiten si no están. No es parte del producto.
"""

from __future__ import annotations

import base64
import json
import random
from pathlib import Path

PLANTILLA = Path(__file__).parents[1] / "src" / "agentreach" / "reporting" / "plantilla_reporte.html"
MARCADOR = "__AGENTREACH_" + "DATA__"
MIN_TEXTO, MIN_GRANDE, MIN_BORDE = 4.5, 3.0, 3.0

_OCULTAR_TEXTO = (
    "*,*::before,*::after{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;"
    "text-decoration-color:transparent!important;caret-color:transparent!important}"
    "svg text,svg tspan{fill:transparent!important;stroke:none!important}html{scroll-behavior:auto!important}"
)

_RECOGER = r"""
() => {
  const textos = [], controles = [], vistos = new Map(); let ids = 0;
  const marcar = el => { let i = el.getAttribute('data-ctm'); if (i === null) { i = String(ids++); el.setAttribute('data-ctm', i); } return i; };
  const num = s => { const m = (s || '').match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const oculto = el => { let op = 1; for (let a = el; a && a !== document.documentElement; a = a.parentElement) {
      const c = getComputedStyle(a); if (c.display === 'none' || c.visibility === 'hidden') return -1; op *= parseFloat(c.opacity); } return op; };
  const sx = scrollX, sy = scrollY;
  for (const el of document.body.querySelectorAll('*')) {
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TITLE'].includes(el.tagName) || el.closest('[aria-hidden="true"]') && !el.closest('svg')) {}
    const op = oculto(el); if (op < 0) continue;
    const cs = getComputedStyle(el);
    const caja = el.getBoundingClientRect();
    if (caja.width <= 2 || caja.height <= 2 || caja.right <= 0 || caja.bottom <= 0) continue;  // texto solo para lector de pantalla o fuera de la página
    // ---- texto propio del elemento
    const nodos = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim());
    if (nodos.length && !['SCRIPT', 'STYLE'].includes(el.tagName)) {
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const n of nodos) { const r = document.createRange(); r.selectNodeContents(n); for (const b of r.getClientRects()) {
        if (b.width < 1 || b.height < 1) continue; x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom); } }
      const svg = el instanceof SVGElement;
      const col = num(svg ? cs.fill : cs.color);
      if (x1 > x0 && col && col[3] > 0 && !(el.closest('[hidden]'))) {
        const key = el.tagName + '.' + (el.getAttribute('class') || '') + '|' + col.join(',') + '|' + cs.fontSize + '|' + cs.fontWeight + '|' + (el.parentElement ? el.parentElement.className : '');
        const item = { x: x0 + sx, y: y0 + sy, w: x1 - x0, h: y1 - y0, fg: [col[0], col[1], col[2], col[3] * op], fs: parseFloat(cs.fontSize), fw: parseInt(cs.fontWeight) || 400,
          key, txt: nodos[0].textContent.trim().slice(0, 40), tag: el.tagName, id: marcar(el) };
        const lista = vistos.get(key) || []; lista.push(item); vistos.set(key, lista);
      }
    }
    // ---- controles con borde
    if (['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'SUMMARY'].includes(el.tagName) || el.getAttribute('role') === 'button' || el.getAttribute('role') === 'tab') {
      const bw = parseFloat(cs.borderTopWidth), bc = num(cs.borderTopColor);
      if (bw >= 1 && cs.borderTopStyle !== 'none' && bc && bc[3] > 0) {
        const r = el.getBoundingClientRect();
        if (r.width > 4 && r.height > 4) controles.push({ id: marcar(el), x: r.left + sx, y: r.top + sy, w: r.width, h: r.height, bw, txt: (el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30),
          key: el.tagName + '.' + (el.getAttribute('class') || '') + '|' + cs.borderTopColor });
      }
    }
  }
  // hasta 3 muestras por tipo de texto (la primera, la del medio y la última, que caen sobre fondos distintos)
  for (const lista of vistos.values()) { lista.sort((a, b) => a.y - b.y); const n = lista.length;
    for (const i of new Set([0, n >> 1, n - 1])) textos.push(lista[i]); }
  const cv = new Map(); for (const c of controles) { const l = cv.get(c.key) || []; l.push(c); cv.set(c.key, l); }
  const cs2 = []; for (const l of cv.values()) { const n = l.length; for (const i of new Set([0, n >> 1, n - 1])) cs2.push(l[i]); }
  return { textos, controles: cs2, alto: document.documentElement.scrollHeight };
}
"""

_UBICAR = r"""
([id, tipo]) => {
  const el = document.querySelector('[data-ctm="' + id + '"]'); if (!el) return null;
  el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  if (tipo === 'texto') {
    for (const n of el.childNodes) { if (n.nodeType !== 3 || !n.textContent.trim()) continue; const r = document.createRange(); r.selectNodeContents(n);
      for (const b of r.getClientRects()) { if (b.width < 1 || b.height < 1) continue; x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom); } }
  } else { const r = el.getBoundingClientRect(); x0 = r.left - 4; y0 = r.top - 4; x1 = r.right + 4; y1 = r.bottom + 4; }
  x0 = Math.max(0, x0); y0 = Math.max(0, y0); x1 = Math.min(innerWidth, x1); y1 = Math.min(innerHeight, y1);
  if (x1 - x0 < 2 || y1 - y0 < 2) return null;
  return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
}
"""

_MEDIR = r"""
async ([b64, tipo, fg, bw]) => {
  const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const g = c.getContext('2d'); g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height).data;
  const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const L = (r, gg, b) => 0.2126 * lin(r) + 0.7152 * lin(gg) + 0.0722 * lin(b);
  const ratio = (a, b) => { const hi = Math.max(a, b), lo = Math.min(a, b); return (hi + 0.05) / (lo + 0.05); };
  const px = (x, y) => { const i = (y * c.width + x) * 4; return [d[i], d[i + 1], d[i + 2]]; };
  if (tipo === 'texto') {
    const out = [];
    for (let y = 1; y < c.height - 1; y++) for (let x = 1; x < c.width - 1; x++) {
      const p = px(x, y), a = fg[3];
      const f = [fg[0] * a + p[0] * (1 - a), fg[1] * a + p[1] * (1 - a), fg[2] * a + p[2] * (1 - a)];
      out.push(ratio(L(f[0], f[1], f[2]), L(p[0], p[1], p[2])));
    }
    out.sort((a, b) => a - b);
    return { min: out[0], p1: out[Math.floor(out.length * 0.01)] };
  }
  // control: se compara la fila del borde (arriba, abajo, izquierda, derecha) con el fondo 2 px afuera; gana la de mejor contraste de cada lado
  // el recorte lleva 4 px de margen y los bordes caen en posiciones fraccionarias: el fondo se toma en la última fila o columna del recorte
  // (3 px o más afuera) y, como un borde punteado deja huecos, se prueban varias columnas o filas y se prueban las filas o columnas vecinas del borde; gana la de mejor contraste de cada lado
  const m = 4, mejores = [], W = c.width, H = c.height, cx = Math.floor(W / 2), cy = Math.floor(H / 2);
  const lados = [
    k => [px(cx + k, 0), j => px(cx + k, m - 2 + j)],
    k => [px(cx + k, H - 1), j => px(cx + k, H - m + 1 - j)],
    k => [px(0, cy + k), j => px(m - 2 + j, cy + k)],
    k => [px(W - 1, cy + k), j => px(W - m + 1 - j, cy + k)],
  ];
  for (const lado of lados) { let mejor = 1;
    for (let k = -8; k <= 8; k++) { const [o, dentro] = lado(k); for (let j = 0; j <= 4; j++) { const i = dentro(j);
      mejor = Math.max(mejor, ratio(L(o[0], o[1], o[2]), L(i[0], i[1], i[2]))); } }
    mejores.push(mejor); }
  return { min: Math.min(...mejores), lados: mejores };
}
"""


def _i18n(en: str, es: str) -> dict:
    return {"en": en, "es": es}


def datos_sinteticos(n: int, semilla: int = 1) -> dict:
    """Datos del esquema v1 con ``n`` hallazgos de Claude Code (y unos pocos de opencode), nombres ficticios y sin secretos."""
    r = random.Random(semilla)
    tipos = {f"TH-{i}": {"title": _i18n(f"Type {i} title", f"Título del tipo {i}")} for i in (1, 2, 3, 5)}
    textos = {k: {"meaning": _i18n(f"{k} means something.", f"{k} significa algo."), "what_to_do": _i18n(f"Do this for {k}.", f"Haga esto para {k}.")} for k in tipos}
    carpetas = ["config", "deploy", ".claude", "docs", "src/api", "src/auth", "services/billing", "infra/dev"]
    if n > 60:
        carpetas += [f"modulos/m{j}/sub" for j in range(30)]

    def hallazgos(prefijo: str, cuantos: int) -> list[dict]:
        salida = []
        for i in range(cuantos):
            ruta = f"{r.choice(carpetas)}/archivo-{i}.env"
            salida.append({"id": f"{prefijo}-{i}", "path": ruta, "line": None if i % 9 == 0 else (i % 80) + 1, "type": r.choice(list(tipos)),
                           "provider": r.choice(["pagos", "nube"]), "level": ["verified", "potential", "potential", "hypothesis"][i % 4],
                           "reason": ["existe", "regla", "no_determinado"][i % 3], "unrelated": r.choice(["no", "si", "no_determinado"]), "agent": None,
                           "posture": r.choice(["sin_regla", "deny"]), "rule": None if i % 2 else ".claude/settings.json:3", "source_verified": False,
                           "text": r.choice(list(tipos))})
        return salida

    agentes = [{"id": "claude_code", "name": "Claude Code", "env_cleaning": False, "rules": [], "findings": hallazgos("cc", n),
                "not_determined": [{"path": "~/.claude/settings.json", "key": "hooks.PreToolUse", "reason": "funcion_no_modelada"},
                                   {"path": ".claude/settings.json", "key": "sandbox", "reason": "funcion_no_modelada"}]},
               {"id": "opencode", "name": "opencode", "env_cleaning": False, "rules": [], "findings": hallazgos("oc", 5)}]
    return {
        "schema_version": 1, "tool": "AgentReach", "tool_version": "0.1.0", "generated_at": "2026-11-10 09:30", "folder": "C:\\\\proyecto\\\\app", "files_looked_at": 41,
        "secrets_notice": _i18n("No secret values are shown. AgentReach never copies passwords.", "No se muestran valores de secretos. AgentReach nunca copia contraseñas."),
        "initial_language": "es",
        "agents": agentes,
        "configured_agents": [{"id": "claude_code", "name": "Claude Code", "evidence": [{"scope": "project", "path": ".claude/settings.json"}, {"scope": "user", "path": "~/.claude/settings.json"}]},
                              {"id": "opencode", "name": "opencode", "evidence": [{"scope": "project", "path": "opencode.json"}]}],
        "catalog": {"types": tipos, "texts": textos,
                    "reasons": {"existe": _i18n("It exists and no rule blocks it.", "Existe y ninguna regla lo bloquea."), "regla": _i18n("A rule blocks it.", "Una regla lo bloquea."),
                    "no_determinado": _i18n("Not determined", "No determinado")},
                    "providers": {"pagos": _i18n("payments service", "servicio de pagos"), "nube": _i18n("cloud account", "cuenta en la nube")},
                    "postures": {"sin_regla": _i18n("no rule", "sin regla"), "deny": _i18n("blocks it (rule only)", "lo bloquea (solo política)"),
                                 "allow": _i18n("allows it", "lo permite"), "ask": _i18n("asks first", "pide confirmación"), "no_determinada": _i18n("not determined", "no determinada")},
                    "unrelated": {"no": _i18n("no", "no"), "si": _i18n("yes", "sí"), "no_determinado": _i18n("not determined", "no determinado")},
                    "no_review": {"funcion_no_modelada": {"title": _i18n("Configuration feature AgentReach does not model", "Función de la configuración que AgentReach no modela"), "how_to_fix": _i18n("Review it by hand.", "Revísala a mano.")}, "archivo_ilegible": {"title": _i18n("Could not open the file", "No se pudo abrir el archivo"), "how_to_fix": _i18n("Check permissions.", "Revise los permisos.")}}},
        "not_reviewed": [{"path": f"datos/bloqueado-{i}.bin", "reason": "archivo_ilegible"} for i in range(4)],
        "limits": {"en": [f"Limit {i} (en)" for i in range(6)], "es": [f"Límite {i} (es)" for i in range(6)]},
        "limits_also": _i18n("Also not covered: other things.", "Tampoco se cubre: otras cosas."),
    }


def pagina(datos: dict) -> str:
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(chr(0x2028), "\\u2028")
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    assert plantilla.count(MARCADOR) == 1
    return plantilla.replace(MARCADOR, js)


def _es_grande(item: dict) -> bool:
    return item["fs"] >= 24 or (item["fs"] >= 18.66 and item["fw"] >= 700)


def _foto(pg, it: dict, tipo: str) -> bytes | None:
    """Lleva el elemento al centro de la ventana y fotografía SOLO su caja (así los elementos fijos o pegajosos salen como se ven)."""
    try:
        clip = pg.evaluate(_UBICAR, [it["id"], tipo])
        return pg.screenshot(clip=clip) if clip else None
    except Exception:  # noqa: BLE001 - recorte vacío o fuera de la página
        return None


def medir_estado(pg, ayudante, etiqueta: str) -> tuple[list[dict], int]:
    """Mide el estado actual de ``pg``. Devuelve (fallos, cuántas medidas)."""
    recogido = pg.evaluate(_RECOGER)
    pg.add_style_tag(content=_OCULTAR_TEXTO)
    pg.wait_for_timeout(150)
    fallos: list[dict] = []
    medidas = 0
    for it in recogido["textos"]:
        if it["w"] < 2 or it["h"] < 2:
            continue
        png = _foto(pg, it, "texto")
        if png is None:
            continue  # texto fuera de la página (dentro de un contenedor con desplazamiento): no se ve, no se mide
        r = ayudante.evaluate(_MEDIR, [base64.b64encode(png).decode(), "texto", it["fg"], 0])
        medidas += 1
        minimo = MIN_GRANDE if _es_grande(it) else MIN_TEXTO
        if r["p1"] < minimo:
            fallos.append({"estado": etiqueta, "clase": "texto", "min": round(r["p1"], 2), "exigido": minimo, "texto": it["txt"], "etiqueta": it["key"], "fg": it["fg"], "y": round(it["y"])})
    for c in recogido["controles"]:
        png = _foto(pg, c, "borde")
        if png is None:
            continue
        r = ayudante.evaluate(_MEDIR, [base64.b64encode(png).decode(), "borde", [0, 0, 0, 1], c["bw"]])
        medidas += 1
        if r["min"] < MIN_BORDE:
            fallos.append({"estado": etiqueta, "clase": "borde", "min": round(r["min"], 2), "exigido": MIN_BORDE, "texto": c["txt"], "etiqueta": c["key"], "lados": [round(x, 2) for x in r["lados"]], "y": round(c["y"])})
    return fallos, medidas
