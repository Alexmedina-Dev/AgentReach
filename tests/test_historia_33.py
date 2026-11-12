"""Historia 33: «Cómo leer este reporte» va primero y siempre visible en el HTML.

Sin navegador: se revisan los datos que viajan en el JSON (glosario ES tú/usted + EN), el orden y el ``open`` de la sección en la plantilla,
el esquema, la copia de la plantilla, la nomenclatura inglesa y la seguridad (canarios, sin recursos externos).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.contracts import Idioma
from agentreach.core.catalogo_explicaciones import Tono
from agentreach.core.catalogo_terminos import FICHAS, Termino, explicacion, linea, nombre
from test_reporte_html import AHORA, ESQUEMA, _validar, datos, finding, html_de, json_de

pytestmark = pytest.mark.sin_tope_por_nombre

RAIZ = Path(__file__).parents[1]
PLANTILLA = RAIZ / "src" / "agentreach" / "reporting" / "plantilla_reporte.html"
COPIA = RAIZ / "docs" / "reporte-html" / "plantilla.html"
PROHIBIDAS = re.compile(r"\bseguro\b|\bsegura\b|inseguro|sin riesgo|\bsafe\b|\bunsafe\b|no risk|risk-free", re.IGNORECASE)


def glosario(**kw) -> dict:
    return json_de(html_de(datos([finding()]), **kw))["glossary"]


def test_el_glosario_trae_las_12_fichas_con_las_tres_variantes():
    assert len(Termino) == 12 and {t["id"] for t in glosario()["terms"]} == {t.value for t in Termino}
    for tono in (Tono.CERCANO, Tono.FORMAL):
        for t in glosario(tono=tono)["terms"]:
            termino = Termino(t["id"])
            assert termino in FICHAS  # término contra entrada
            for idioma, clave in ((Idioma.ES, "es"), (Idioma.EN, "en")):
                esperado = {"name": nombre(termino, idioma), "line": linea(termino, idioma, tono)}
                esperado["what_is"], esperado["means"], esperado["to_do"] = explicacion(termino, idioma, tono)
                for campo, texto in esperado.items():
                    assert t[campo][clave] == texto and texto.strip(), (t["id"], campo, clave)


def test_niveles_con_el_significado_completo_y_el_camino_de_alcance():
    g = {t["id"]: t for t in glosario()["terms"]}
    assert "sin abrirlo para probarlo." in g["nivel_comprobado"]["what_is"]["es"]
    assert (
        "no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, "
        "no una barrera real del sistema)."
    ) in g["nivel_potencial"]["what_is"]["es"]
    assert "Verified" in g["nivel_comprobado"]["line"]["en"] and "Potential" in g["nivel_potencial"]["line"]["en"]
    assert "Hypothesis" in g["nivel_hipotesis"]["line"]["en"]
    c = g["camino_de_alcance"]
    assert c["name"] == {"es": "Camino de alcance", "en": "Reach route"}
    assert "Agente → Dónde → Qué hay → Efecto posible" in c["what_is"]["es"]
    assert "Agent → Where → What is there → Possible effect" in c["what_is"]["en"]
    assert "línea continua" in c["means"]["es"] and "línea discontinua" in c["means"]["es"]
    assert "solid line" in c["means"]["en"] and "dashed line" in c["means"]["en"]


def test_el_tono_cambia_el_espanol_y_no_el_ingles():
    cercano, formal = glosario(tono=Tono.CERCANO), glosario(tono=Tono.FORMAL)
    assert cercano["labels"]["means"]["es"] == "Qué significa para ti" and formal["labels"]["means"]["es"] == "Qué significa para usted"
    assert cercano["labels"]["to_do"]["es"] == "Qué puedes hacer" and formal["labels"]["to_do"]["es"] == "Qué puede hacer"
    c, f = ({t["id"]: t for t in g["terms"]}["camino_de_alcance"] for g in (cercano, formal))
    assert c["to_do"]["es"].startswith("empieza por") and f["to_do"]["es"].startswith("empiece por")
    assert c["to_do"]["en"] == f["to_do"]["en"]
    assert cercano["labels"]["means"]["en"] == formal["labels"]["means"]["en"] == "What it means for you"


def test_ningun_texto_del_glosario_dice_seguro():
    for tono in (Tono.CERCANO, Tono.FORMAL):
        assert not PROHIBIDAS.search(json.dumps(glosario(tono=tono), ensure_ascii=False))


def test_el_esquema_acepta_el_glosario_y_sigue_aceptando_un_reporte_sin_el():
    cargado = json_de(html_de(datos([finding()])))
    _validar(cargado, ESQUEMA)
    _validar({k: v for k, v in cargado.items() if k != "glossary"}, ESQUEMA)


def test_la_plantilla_y_su_copia_en_docs_son_identicas():
    assert PLANTILLA.read_text(encoding="utf-8") == COPIA.read_text(encoding="utf-8")


def test_la_seccion_va_primero_tras_la_cabecera_abierta_y_antes_del_resumen():
    h = html_de(datos([finding()]))
    cuerpo = h.split("</header>", 1)[1]
    assert cuerpo.index('id="howto"') < cuerpo.index('id="cfg"') < cuerpo.index('id="summary"')
    primero = re.search(r"<(?:section|div|aside|main)\b[^>]*>", cuerpo.split('<div class="wrap">', 1)[1])
    assert primero and 'id="howto"' in primero.group(0) and "setAttribute('aria-labelledby','howTitle')" in h
    # el <details> sale abierto por defecto (y conserva lo que la persona pliega); los demás términos, plegados
    assert "wasOpen=prev?prev.open:true" in h and "'<details id=\"howDetails\"'+(wasOpen?' open':'')" in h
    assert "HOW_OPEN=['nivel_comprobado','nivel_potencial','nivel_hipotesis','camino_de_alcance']" in h
    assert "(openIds.has(x.id)?' open':'')" in h
    assert "beforeprint" in h and "d.open=true" in h  # en papel sale abierta


def test_sin_hallazgos_la_seccion_tambien_esta():
    h = html_de(datos([]))
    assert 'id="howto"' in h and "glossary" in json_de(h)


# «path» en inglés solo puede ser una ruta de archivo; estos son los únicos contextos permitidos (el resto es el camino y debe decir «route»)
RUTA_DE_ARCHIVO = ("Copy path:line", "alphabetical order of path", "path levels")


def _bloque_en(plantilla: str) -> str:
    return plantilla.split("\n es:{skip", 1)[0].split("\n en:{skip", 1)[1]


def _textos_visibles_en_ingles(plantilla: str) -> list[str]:
    """Todo el texto inglés de la plantilla: el marcado estático (sin etiquetas, estilos ni scripts), título, descripción y el bloque ``en:``."""
    estatico = re.sub(r"<style.*?</style>|<script.*?</script>|<svg.*?</svg>", " ", plantilla.split("</head>", 1)[1], flags=re.DOTALL)
    estatico = re.sub(r"<[^>]+>", " ", estatico)
    meta = re.findall(r"<title>(.*?)</title>|<meta name=\"description\" content=\"(.*?)\"", plantilla)
    cadenas = re.findall(r"'((?:[^'\\]|\\.)*)'", _bloque_en(plantilla))  # solo literales: no cuentan claves como ``paths:`` o ``modePaths:``
    return [estatico, *[a or b for a, b in meta], *cadenas]


def test_en_ingles_el_camino_es_reach_route_y_la_vista_route_map():
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    ingles = _bloque_en(plantilla)
    assert "graph:'Route map'" in ingles and "Reach <span>route</span>" in ingles and "total:'Routes'" in ingles
    assert 'id="skip">Skip to the routes</a>' in plantilla
    for texto in _textos_visibles_en_ingles(plantilla):
        for m in re.finditer(r"\b[Pp]aths?\b", texto):
            contexto = texto[max(0, m.start() - 30) : m.end() + 30]
            assert any(ok in contexto for ok in RUTA_DE_ARCHIVO), contexto
    assert "Reach path" not in plantilla and "Reach route report" in plantilla


def test_los_ids_de_how_open_son_terminos_del_catalogo():
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    ids = re.search(r"HOW_OPEN=\[(.*?)\]", plantilla).group(1)
    ids = re.findall(r"'([a-z_]+)'", ids)
    assert len(ids) == 4 and set(ids) <= {t.value for t in Termino}


def test_los_textos_de_la_seccion_no_estan_escritos_a_mano_en_la_plantilla():
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    for frase in ("sin abrirlo para probarlo", "Agente → Dónde", "Agent → Where", "trazo continuo"):
        assert frase not in plantilla


def test_el_html_con_tono_formal_lleva_usted_y_no_filtra_canarios(tmp_path: Path):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=ZQX-ENV-123456\n", encoding="utf-8")
    destino = tmp_path / "r.html"
    assert cli.main([str(proyecto), "--formato", "html", "--salida", str(destino), "--tono", "formal"], ahora=lambda: AHORA) in (0, 1)
    texto = destino.read_text(encoding="utf-8")
    g = json.loads(re.search(r'id="data">(.*?)</script>', texto, re.DOTALL).group(1))["glossary"]
    assert g["labels"]["means"]["es"] == "Qué significa para usted"
    assert "ZQX" not in texto and "123456" not in texto
    for prohibido in ("http://", "https://", "<link", "<img", "@import"):
        assert prohibido not in texto
