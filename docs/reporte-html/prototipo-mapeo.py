"""Reference mapper (prototype of src/agentreach/reporting/html.py): synthetic views -> template JSON -> HTML.
usage: build_data.py OUT.html N_CLAUDE N_OPENCODE [--hostile]
"""
import json, random, sys
sys.path.insert(0, "src")
from agentreach.contracts import *  # noqa
from agentreach.contracts.finding import Tipo, Nivel, Motivo, Ajeno, Postura, Proveedor, texto_de_motivo, Idioma
from agentreach.core import catalogo_explicaciones as C

ES, EN = Idioma.ES, Idioma.EN
def bi(f):  # f(idioma) -> {"en","es"}
    return {"en": f(EN), "es": f(ES)}

out, nc, no = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
hostile = "--hostile" in sys.argv
rnd = random.Random(3)
tipos = list(Tipo); niveles = [Nivel.COMPROBADO] * 2 + [Nivel.POTENCIAL] * 4 + [Nivel.HIPOTESIS] * 4

catalog = {"types": {}, "texts": {}, "reasons": {}, "providers": {}, "postures": {}, "unrelated": {}, "no_review": {}}
for t in Tipo:
    catalog["types"][t.value] = {"title": bi(lambda i: C.titulo_corto(t, i))}
    catalog["texts"][t.value] = {"meaning": bi(lambda i: C.que_significa(t, Ajeno.NO, i)), "what_to_do": bi(lambda i: C.que_hacer(t, i))}
for m in Motivo: catalog["reasons"][m.value] = bi(lambda i: texto_de_motivo(m, i))
for p in Proveedor: catalog["providers"][p.value] = bi(lambda i: C.PROVEEDOR[p][i])
for p in Postura: catalog["postures"][p.value] = bi(lambda i: C.POSTURA[p][i])
for a in Ajeno: catalog["unrelated"][a.value] = bi(lambda i: C.AJENO[a][i])
for m in MotivoNoRevisado:
    catalog["no_review"][m.value] = {"title": bi(lambda i: C.TITULO_MOTIVO[m][i]), "how_to_fix": bi(lambda i: C.COMO_RESOLVER[m][i])}
# TH-17 meaning varies with "unrelated": own text keys
for a in (Ajeno.SI, Ajeno.NO_DETERMINADO):
    catalog["texts"]["TH-17/" + a.value] = {"meaning": bi(lambda i: C.que_significa(Tipo.SECRETO_DE_ALTO_PODER, a, i)),
                                          "what_to_do": bi(lambda i: C.que_hacer(Tipo.SECRETO_DE_ALTO_PODER, i))}

def findings(n, tag, labels):
    fs = []
    for i in range(n):
        t = rnd.choice(tipos); lv = rnd.choice(niveles); aj = rnd.choice(list(Ajeno))
        path = "src/" + "/".join("pkg%d" % rnd.randint(1, 9) for _ in range(rnd.randint(1, 3))) + "/file%d.example" % i
        if i % 17 == 0: path = "docs/" + "very-long-folder-name-" * 8 + "end/f%d.example" % i
        if hostile and i == 0: path = "src/</script><img src=x onerror=alert(1)>\x1b[2J\u202egnp.exe"
        text = t.value + ("/" + aj.value if t is Tipo.SECRETO_DE_ALTO_PODER and aj is not Ajeno.NO else "")
        po = rnd.choice(list(Postura)); rule = "config/rules.example:%d" % rnd.randint(1, 50) if po in (Postura.ALLOW, Postura.ASK, Postura.DENY) else None
        fs.append({"id": "%s-%d" % (tag, i), "path": path, "line": None if i % 9 == 0 else rnd.randint(1, 900), "type": t.value,
                   "provider": rnd.choice(list(Proveedor)).value, "level": {"comprobado": "verified", "potencial": "potential", "hipotesis": "hypothesis"}[lv.value],
                   "reason": rnd.choice(list(Motivo)).value, "unrelated": aj.value, "agent": rnd.choice(labels),
                   "posture": po.value, "rule": rule, "source_verified": False, "text": text})
    return fs

nr = [{"path": "data/locked%d.example" % i, "reason": rnd.choice(list(MotivoNoRevisado)).value} for i in range(7)]
if hostile: nr.append({"path": "x\u202e\x1b]0;pwn\x07.txt", "reason": "archivo_ilegible"})
data = {
    "schema_version": 1, "tool": "AgentReach", "tool_version": "0.1.0", "generated_at": "2026-11-10 09:30", "folder": "~/demo-app (fictional)", "files_looked_at": 412,
    "secrets_notice": {"en": "No secret values are shown. AgentReach never copies passwords, tokens or keys: it only says where they are and what type they are.",
                       "es": "No se muestran valores de secretos. AgentReach nunca copia contraseñas, tokens ni claves: solo dice dónde están y de qué tipo son."},
    "agents": [
        {"id": "claude_code", "name": "Claude Code", "env_cleaning": False,
         "rules": [{"posture": "allow", "tool": "Bash(git *)", "location": "~/.claude/settings.json:12"}, {"posture": "ask", "tool": "Edit", "location": ".claude/settings.json:4"}],
         "findings": findings(nc, "cc", ["main", "reviewer", None])},
        {"id": "opencode", "name": "opencode", "env_cleaning": True, "rules": [], "findings": findings(no, "oc", ["build", None])},
        {"id": "none", "name": {"en": "Not tied to a specific agent", "es": "Sin agente específico"}, "env_cleaning": False, "rules": [], "findings": findings(2, "na", [None])},
    ],
    "catalog": catalog, "not_reviewed": nr,
    "limits": {"en": list(C.LIMITES[EN]), "es": list(C.LIMITES[ES])},
    "limits_also": {"en": C.LIMITES_TAMBIEN[EN], "es": C.LIMITES_TAMBIEN[ES]},
}
if no == 0: data["agents"][1]["findings"] = []
txt = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
tpl = open("docs/reporte-html/plantilla.html", encoding="utf-8").read()
assert tpl.count("__AGENTREACH_DATA__") == 1
open(out, "w", encoding="utf-8").write(tpl.replace("__AGENTREACH_DATA__", txt))
open(out + ".json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))
print("ok", len(txt))
