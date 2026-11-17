"""Historia 31: aviso de versión nueva.

Al abrir, como máximo cada 15 días, AgentReach consulta por internet SOLO el número de la última versión. Nada de la persona ni de su
carpeta. Nunca durante la revisión. Sin internet, con un error o sin terminal, calla. Las pruebas no tocan la red: ponen respuestas falsas.
"""

from __future__ import annotations

import ast
import json
import subprocess
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.cli import reportes
from agentreach.infra import actualizacion as act

AHORA = datetime(2026, 11, 17, 9, 0, 0)
NUEVA = "9.9.9"


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / "README.md").write_text("hola\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto}


class Mundo:
    """Un ejemplo de uso completo con las costuras de ``cli`` falsas: cuántas veces se consultó, qué se preguntó y si se instaló."""

    def __init__(self, monkeypatch, respuesta_version=NUEVA, a_la_pregunta="s", con_uv=True, instala=True):
        self.consultas: list[str] = []
        self.instalaciones = 0
        self.textos: list[str] = []
        self.orden: list[str] = []
        self.a_la_pregunta = a_la_pregunta
        monkeypatch.setattr(cli, "_comprobar_version_por_defecto", True)

        def consultar(actual: str):
            self.consultas.append(actual)
            self.orden.append("consulta")
            if isinstance(respuesta_version, Exception):
                raise respuesta_version
            return respuesta_version

        def instalar():
            self.instalaciones += 1
            self.orden.append("instala")
            return instala

        monkeypatch.setattr(cli, "_consultar_version", consultar)
        monkeypatch.setattr(cli, "_instalar_version", instalar)
        monkeypatch.setattr(cli, "_instalado_con_uv", lambda: con_uv)

    def preguntar(self, texto: str) -> str:
        self.textos.append(texto)
        if "Descargarla ahora" in texto or "Download it now" in texto:
            self.orden.append("pregunta-version")
            return self.a_la_pregunta if isinstance(self.a_la_pregunta, str) else self.a_la_pregunta.pop(0)
        if "lea esta carpeta" in texto or "allowed to read this folder" in texto:
            self.orden.append("pregunta-carpeta")
            return "s" if "(S/N)" in texto else "y"
        if "AgentReach necesita ver" in texto or "AgentReach needs to see" in texto:
            return "n"  # lo del segundo nivel no importa aquí
        return "n"

    def correr(self, mundo, *extra, ahora=AHORA) -> int:
        return cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html", *extra],
                        ahora=lambda: ahora, preguntar=self.preguntar)

    def pregunto_version(self) -> int:
        return sum(1 for t in self.textos if "Descargarla ahora" in t or "Download it now" in t)


def preferencias(mundo) -> dict:
    return json.loads((mundo["casa"] / reportes.CARPETA / "preferencias.json").read_text(encoding="utf-8"))


# ---- el número de versión: expresión estricta --------------------------------------------------------------------------------------


@pytest.mark.parametrize("texto", ["0.1.0", "1.2.3", "10.20.30", "0.1.0.dev0", "1.0.0.dev12", "9999.9999.9999"])
def test_versiones_validas(texto):
    assert act.version_valida(texto)


@pytest.mark.parametrize("texto", ["", "1", "1.2", "1.2.3.4", "1.2.3rc1", "v1.2.3", "1.2.3\n", " 1.2.3", "1.2.3; rm -rf /", "1.2.3 && echo",
                                   "$(whoami)", "1.2.3\x1b[31m", "١.٢.٣", "1.2.3.dev", "1.2.3.dev12345", "99999.1.1", "-1.2.3", "1.2.3-beta",
                                   "<script>", "1.2.3\r\nX: y", "1." + "2" * 40 + ".3"])
def test_versiones_que_no_se_aceptan(texto):
    assert not act.version_valida(texto)
    assert not act.es_mas_nueva(texto, "0.0.1")


@pytest.mark.parametrize("ultima, actual, nueva", [("0.2.0", "0.1.0", True), ("1.0.0", "0.9.9", True), ("0.1.1", "0.1.0", True),
                                                   ("0.1.0", "0.1.0", False), ("0.1.0.dev0", "0.1.0", False), ("0.0.9", "0.1.0", False),
                                                   ("0.1.0", "0.0.0", True), ("10.0.0", "9.9.9", True), ("1.2.3", "no entendida", False)])
def test_comparacion_numerica(ultima, actual, nueva):
    assert act.es_mas_nueva(ultima, actual) is nueva


# ---- la consulta: HTTPS, github.com, sin redirecciones a otros sitios, sin datos ------------------------------------------------------


class _Respuesta:
    def __init__(self, cuerpo: bytes, status=200, url=act.URL_VERSION):
        self._cuerpo, self.status, self._url = cuerpo, status, url

    def read(self, n=-1):
        return self._cuerpo if n < 0 else self._cuerpo[:n]

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Abridor:
    def __init__(self, resultado):
        self.resultado, self.peticiones, self.tiempos = resultado, [], []

    def open(self, peticion, timeout=None):
        self.peticiones.append(peticion)
        self.tiempos.append(timeout)
        if isinstance(self.resultado, Exception):
            raise self.resultado
        return self.resultado


def _con_abridor(monkeypatch, resultado) -> _Abridor:
    abridor = _Abridor(resultado)
    monkeypatch.setattr(urllib.request, "build_opener", lambda *a, **k: abridor)
    return abridor


def test_la_direccion_es_https_en_github_y_fija():
    assert act.URL_VERSION.startswith("https://github.com/Alexmedina-Dev/AgentReach/")
    assert act.URL_VERSION.endswith("pyproject.toml") and "http://" not in act.URL_VERSION


def test_la_peticion_no_lleva_nada_de_la_persona(monkeypatch):
    abridor = _con_abridor(monkeypatch, _Respuesta(b'[project]\nname = "agentreach"\nversion = "1.2.3"\n'))
    assert act.consultar("0.1.0") == "1.2.3"
    [peticion] = abridor.peticiones
    assert peticion.full_url == act.URL_VERSION and peticion.get_method() == "GET" and peticion.data is None
    assert dict(peticion.header_items()) == {"User-agent": "AgentReach/0.1.0"}  # solo el nombre del programa y su versión
    assert abridor.tiempos == [4.0]  # con tiempo límite


@pytest.mark.parametrize("cuerpo", [b"", b"no es toml", b'version = "malo"', b'version = "1.2.3; rm -rf /"', b'version = "1.2"',
                                    b'name = "x"\n# version = "1.2.3"\n', b"\xff\xfe\x00\x00", b"x" * 200000])
def test_un_cuerpo_que_no_se_entiende_da_none(monkeypatch, cuerpo):
    _con_abridor(monkeypatch, _Respuesta(cuerpo))
    assert act.consultar("0.1.0") is None


def test_solo_se_lee_un_trozo_pequeno(monkeypatch):
    relleno = b"# " + b"x" * 70000 + b'\nversion = "5.5.5"\n'
    _con_abridor(monkeypatch, _Respuesta(relleno))
    assert act.consultar("0.1.0") is None  # el número está después del límite de lectura: no se busca más allá


@pytest.mark.parametrize("error", [urllib.error.URLError("sin internet"), TimeoutError(), OSError("x"), ValueError("x"),
                                   urllib.error.HTTPError(act.URL_VERSION, 404, "no", {}, None)])
def test_sin_internet_o_con_error_da_none_sin_fallar(monkeypatch, error):
    _con_abridor(monkeypatch, error)
    assert act.consultar("0.1.0") is None


def test_un_estado_que_no_es_200_o_una_url_que_no_es_https_da_none(monkeypatch):
    _con_abridor(monkeypatch, _Respuesta(b'version = "1.2.3"', status=204))
    assert act.consultar("0.1.0") is None
    _con_abridor(monkeypatch, _Respuesta(b'version = "1.2.3"', url="http://github.com/x"))
    assert act.consultar("0.1.0") is None


@pytest.mark.parametrize("destino, permitido", [
    ("https://raw.githubusercontent.com/Alexmedina-Dev/AgentReach/main/pyproject.toml", True),
    ("https://github.com/otra/ruta", True),
    ("http://raw.githubusercontent.com/x", False),
    ("http://github.com/x", False),
    ("https://evil.example/x", False),
    ("https://github.com.evil.example/x", False),
    ("https://raw.githubusercontent.com.evil.example/x", False),
    ("https://usuario@github.com/x", False),
    ("https://github.com:8443/x", False),
    ("ftp://github.com/x", False),
    ("file:///etc/passwd", False),
    ("//evil.example/x", False),
])
def test_solo_se_sigue_la_redireccion_de_github_a_su_servidor_de_archivos(destino, permitido):
    manejador = act._SoloRedireccionDeGitHub()
    peticion = urllib.request.Request(act.URL_VERSION)
    if permitido:
        assert manejador.redirect_request(peticion, None, 302, "Found", {}, destino) is not None
    else:
        with pytest.raises(urllib.error.HTTPError):
            manejador.redirect_request(peticion, None, 302, "Found", {}, destino)
    assert manejador.max_redirections == 1


# ---- el comando exacto y la instalación --------------------------------------------------------------------------------------------


def test_el_comando_exacto():
    assert " ".join(act.COMANDO) == "uv tool install --reinstall git+https://github.com/Alexmedina-Dev/AgentReach"
    assert "upgrade" not in " ".join(act.COMANDO)  # uv tool upgrade no está verificado para instalaciones desde git


def test_instalar_corre_uv_sin_shell_con_tiempo_limite_y_sin_entrada(monkeypatch):
    visto = {}
    monkeypatch.setattr(act.shutil, "which", lambda nombre: "C:/uv/uv.exe")

    def falso(argumentos, **k):
        visto.update(args=argumentos, **k)
        return subprocess.CompletedProcess(argumentos, 0)

    monkeypatch.setattr(act.subprocess, "run", falso)
    assert act.instalar() is True
    assert visto["args"] == ["C:/uv/uv.exe", "tool", "install", "--reinstall", act.REPOSITORIO]
    assert visto["shell"] is False and visto["timeout"] and visto["stdin"] is subprocess.DEVNULL


@pytest.mark.parametrize("fallo", [subprocess.TimeoutExpired("uv", 1), OSError("x"), subprocess.SubprocessError("x")])
def test_si_la_instalacion_falla_da_false(monkeypatch, fallo):
    monkeypatch.setattr(act.shutil, "which", lambda nombre: "uv")

    def falla(*a, **k):
        raise fallo

    monkeypatch.setattr(act.subprocess, "run", falla)
    assert act.instalar() is False


def test_instalar_con_codigo_distinto_de_cero_o_sin_uv_da_false(monkeypatch):
    monkeypatch.setattr(act.shutil, "which", lambda nombre: "uv")
    monkeypatch.setattr(act.subprocess, "run", lambda a, **k: subprocess.CompletedProcess(a, 1))
    assert act.instalar() is False
    monkeypatch.setattr(act.shutil, "which", lambda nombre: None)
    assert act.instalar() is False


@pytest.mark.parametrize("prefijo, con_uv, esperado", [
    (r"C:\Users\x\AppData\Roaming\uv\tools\agentreach", True, True),
    (r"C:\Users\x\AppData\Roaming\uv\tools\agentreach", False, False),  # uv no está en el PATH
    (r"C:\proyecto\.venv", True, False),
    (r"C:\Python313", True, False),
    (r"C:\Users\x\AppData\Roaming\uv\tools\otra-herramienta", True, False),
])
def test_solo_se_reinstala_si_esta_instalado_con_uv(monkeypatch, prefijo, con_uv, esperado):
    monkeypatch.setattr(act.sys, "prefix", prefijo)
    monkeypatch.setattr(act.os, "sep", "\\")
    monkeypatch.setattr(act.os.path, "normpath", lambda p: p)
    monkeypatch.setattr(act.shutil, "which", lambda nombre: "uv" if con_uv else None)
    assert act.instalado_con_uv() is esperado


# ---- el flujo en la línea de comandos ----------------------------------------------------------------------------------------------


def test_con_version_nueva_dice_cual_muestra_el_comando_y_pregunta_con_letras_en_mayuscula(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="n")
    m.correr(mundo)
    salida = capsys.readouterr().err
    assert f"Hay una versión nueva ({NUEVA})." in salida
    assert "Comando exacto:\n  uv tool install --reinstall git+https://github.com/Alexmedina-Dev/AgentReach" in salida
    assert "¿Descargarla ahora? (S/N) " in m.textos


def test_en_ingles(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="n")
    m.correr(mundo, "--idioma", "en")
    salida = capsys.readouterr().err
    assert f"There is a new version ({NUEVA})." in salida and "Exact command:\n  uv tool install --reinstall" in salida
    assert "Download it now? (Y/N) " in m.textos


def test_con_s_instala_al_terminar_y_no_durante_la_revision(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="s")
    llamadas = []
    original = cli.auditar

    def vigilada(*a, **k):
        llamadas.append("auditar-empieza")
        m.orden.append("auditar-empieza")
        try:
            return original(*a, **k)
        finally:
            m.orden.append("auditar-termina")

    monkeypatch.setattr(cli, "auditar", vigilada)
    m.correr(mundo)
    assert m.instalaciones == 1
    assert m.orden.index("consulta") < m.orden.index("auditar-empieza")
    assert m.orden.index("instala") > m.orden.index("auditar-termina")  # al terminar el programa
    assert m.orden[-1] == "instala"
    assert "Listo: la versión nueva" in capsys.readouterr().err


def test_con_s_pero_sin_uv_solo_muestra_el_comando(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="s", con_uv=False)
    m.correr(mundo)
    assert m.instalaciones == 0
    salida = capsys.readouterr().err
    assert "uv tool install --reinstall git+https://github.com/Alexmedina-Dev/AgentReach" in salida.split("Para hacerlo a mano")[-1]


def test_con_s_y_la_instalacion_falla_muestra_el_comando_y_no_falla(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="S", instala=False)
    assert m.correr(mundo) in (0, 1)
    assert m.instalaciones == 1 and "a mano" in " ".join(capsys.readouterr().err.split())


def test_con_n_sigue_con_la_actual_y_no_instala(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, a_la_pregunta="N")
    assert m.correr(mundo) in (0, 1)
    assert m.instalaciones == 0 and "Reporte de revisión" in capsys.readouterr().out


def test_con_n_vuelve_a_avisar_a_los_15_dias_y_no_antes(mundo, monkeypatch):
    m = Mundo(monkeypatch, a_la_pregunta="n")
    m.correr(mundo)
    assert len(m.consultas) == 1 and preferencias(mundo)["ultima_comprobacion_de_version"] == AHORA.date().isoformat()
    m.correr(mundo, ahora=AHORA + timedelta(days=14))
    assert len(m.consultas) == 1  # a los 14 días no consulta
    m.correr(mundo, ahora=AHORA + timedelta(days=15))
    assert len(m.consultas) == 2 and m.pregunto_version() == 2  # a los 15, sí, y vuelve a avisar


def test_con_s_tambien_se_espacia(mundo, monkeypatch):
    m = Mundo(monkeypatch, a_la_pregunta="s")
    m.correr(mundo)
    m.correr(mundo, ahora=AHORA + timedelta(days=1))
    assert len(m.consultas) == 1


@pytest.mark.parametrize("respuestas", [[""] * 3, ["si"] * 3, ["yes", "", " s"], ["\n", "x", "1"]])
def test_enter_y_otras_cosas_no_deciden_y_tras_tres_intentos_no_se_instala(mundo, monkeypatch, respuestas):
    m = Mundo(monkeypatch, a_la_pregunta=list(respuestas))
    assert m.correr(mundo) in (0, 1)
    assert m.pregunto_version() == 3 and m.instalaciones == 0


def test_solo_s_S_n_N_en_espanol_y_y_Y_en_ingles(mundo, monkeypatch):
    for letra, instala in [("s", 1), ("S", 1), ("n", 0), ("N", 0)]:
        m = Mundo(monkeypatch, a_la_pregunta=letra)
        m.correr(mundo, ahora=AHORA + timedelta(days=100 * (1 + "sSnN".index(letra))))
        assert m.instalaciones == instala, letra
    m = Mundo(monkeypatch, a_la_pregunta=["s", "s", "s"])
    m.correr(mundo, "--idioma", "en", ahora=AHORA + timedelta(days=1000))
    assert m.instalaciones == 0  # en inglés una «s» no vale


@pytest.mark.parametrize("version", [None, "0.0.1", "0.1.0", "no es una versión"])
def test_sin_version_nueva_o_sin_entenderla_no_dice_nada(mundo, monkeypatch, capsys, version):
    m = Mundo(monkeypatch, respuesta_version=version)
    assert m.correr(mundo) in (0, 1)
    assert m.pregunto_version() == 0 and "versión nueva" not in capsys.readouterr().err


def test_si_la_consulta_falla_con_un_error_no_avisa_ni_falla(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch, respuesta_version=RuntimeError("boom"))
    assert m.correr(mundo) in (0, 1)
    salida = capsys.readouterr()
    assert m.pregunto_version() == 0 and "Error interno" not in salida.out + salida.err


@pytest.mark.parametrize("contenido", ["esto no es json", "[1, 2]", '{"ultima_comprobacion_de_version": 5}',
                                       '{"ultima_comprobacion_de_version": "ayer"}', '{"ultima_comprobacion_de_version": "9999-99-99"}',
                                       '{"ultima_comprobacion_de_version": "2099-01-01"}', "", "\x00\x00"])
def test_un_archivo_de_preferencias_corrupto_no_falla_y_se_arregla(mundo, monkeypatch, contenido):
    carpeta = mundo["casa"] / reportes.CARPETA
    carpeta.mkdir()
    (carpeta / "preferencias.json").write_text(contenido, encoding="utf-8")
    m = Mundo(monkeypatch, a_la_pregunta="n")
    assert m.correr(mundo) in (0, 1)
    assert len(m.consultas) == 1  # una fecha ilegible o en el futuro cuenta como «toca consultar»
    assert preferencias(mundo)["ultima_comprobacion_de_version"] == AHORA.date().isoformat()


def test_la_fecha_no_pisa_la_otra_preferencia_y_viceversa(mundo):
    casa, proyecto = str(mundo["casa"]), str(mundo["proyecto"])
    assert reportes.guardar_preferencia(casa, proyecto, True)
    assert reportes.guardar_comprobacion(casa, proyecto, date(2026, 11, 17))
    assert preferencias(mundo) == {"abrir_en_navegador": True, "ultima_comprobacion_de_version": "2026-11-17"}
    assert reportes.guardar_preferencia(casa, proyecto, False)
    assert reportes.leer_comprobacion(casa, proyecto) == date(2026, 11, 17)
    assert reportes.leer_preferencia(casa, proyecto) is False


def test_sin_poder_anotar_la_fecha_no_se_consulta(mundo, monkeypatch):
    m = Mundo(monkeypatch)
    monkeypatch.setattr(cli, "guardar_comprobacion", lambda *a, **k: False)
    m.correr(mundo)
    assert m.consultas == []


def test_la_fecha_va_en_la_carpeta_de_reportes_fuera_de_la_carpeta_revisada(mundo, monkeypatch):
    Mundo(monkeypatch, a_la_pregunta="n").correr(mundo)
    assert (mundo["casa"] / reportes.CARPETA / "preferencias.json").is_file()
    assert sorted(p.name for p in mundo["proyecto"].iterdir()) == ["README.md"]  # el proyecto sigue igual


# ---- los silencios y los interruptores ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("extra", [["--sin-actualizar"], ["--formato", "html", "--salida", "SALIDA.html"], ["--salida", "SALIDA.txt"]])
def test_no_consulta_con_sin_actualizar_ni_con_formato_ni_con_salida(mundo, monkeypatch, tmp_path, extra):
    m = Mundo(monkeypatch)
    extra = [str(tmp_path / e) if e.startswith("SALIDA") else e for e in extra]
    m.correr(mundo, *extra)
    assert m.consultas == [] and not (mundo["casa"] / reportes.CARPETA / "preferencias.json").exists()


@pytest.mark.parametrize("valor", ["1", "si", "x"])
def test_la_variable_de_entorno_apaga_la_consulta(mundo, monkeypatch, valor):
    monkeypatch.setenv("AGENTREACH_SIN_ACTUALIZAR", valor)
    m = Mundo(monkeypatch)
    m.correr(mundo)
    assert m.consultas == []


def test_sin_terminal_no_lee_nada_ni_consulta(mundo, monkeypatch, capsys):
    m = Mundo(monkeypatch)
    monkeypatch.setattr(cli, "_interactivo", lambda: False)
    assert m.correr(mundo) == 2
    assert m.consultas == [] and "sin una terminal interactiva" in " ".join(capsys.readouterr().err.split())


def test_la_ayuda_la_version_y_el_doctor_no_consultan(mundo, monkeypatch):
    m = Mundo(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    cli.main(["doctor", str(mundo["proyecto"])])
    assert m.consultas == []


def test_con_la_opcion_en_la_ayuda():
    assert "--sin-actualizar" in cli.construir_parser().format_help()


def test_la_consulta_nunca_ocurre_durante_la_revision(mundo, monkeypatch):
    """La consulta es antes de la revisión y, mientras corre la revisión, intentarla fallaría: la bandera la vigila."""
    m = Mundo(monkeypatch, a_la_pregunta="n")
    dentro = {"en_revision": False}
    original = cli.auditar

    def vigilada(*a, **k):
        dentro["en_revision"] = True
        try:
            return original(*a, **k)
        finally:
            dentro["en_revision"] = False

    def consultar(actual):
        assert not dentro["en_revision"], "se consultó la red durante la revisión"
        return NUEVA

    monkeypatch.setattr(cli, "auditar", vigilada)
    monkeypatch.setattr(cli, "_consultar_version", consultar)
    m.correr(mundo)


def test_la_revision_sigue_sin_red_aunque_exista_el_aviso(mundo, monkeypatch):
    """Con el aviso apagado (como en la revisión), no se abre NINGÚN socket ni se resuelve ningún nombre durante toda la ejecución."""
    import socket

    intentos: list[str] = []

    def trampa(nombre):
        def f(*a, **k):
            intentos.append(nombre)
            raise AssertionError(f"red: {nombre}")
        return f

    for nombre in ("socket", "create_connection", "getaddrinfo", "gethostbyname", "getnameinfo"):
        monkeypatch.setattr(socket, nombre, trampa(nombre))
    monkeypatch.setattr(cli, "_comprobar_version_por_defecto", False)
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html"], ahora=lambda: AHORA,
                    preguntar=lambda t: "n") in (0, 1, 2)
    monkeypatch.setattr(cli, "_comprobar_version_por_defecto", True)
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html", "--sin-actualizar"], ahora=lambda: AHORA,
                    preguntar=lambda t: "n") in (0, 1, 2)
    assert intentos == []


def test_con_el_aviso_encendido_la_unica_via_de_red_es_la_consulta(mundo, monkeypatch):
    """Si la consulta real corre con la red bloqueada, falla en silencio y la revisión sigue igual."""
    import socket

    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: (_ for _ in ()).throw(OSError("sin red")))
    monkeypatch.setattr(cli, "_comprobar_version_por_defecto", True)
    monkeypatch.setattr(cli, "_consultar_version", act.consultar)
    textos: list[str] = []

    def preguntar(t):
        textos.append(t)
        return "s" if "lea esta carpeta" in t else "n"

    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html"], ahora=lambda: AHORA, preguntar=preguntar) in (0, 1)
    assert not any("Descargarla" in t for t in textos)


# ---- transparencia ------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("idioma, frases", [
    ("es", ["15 días", "dirección IP", "la hora", "nombre del programa", "revela que esa IP usa AgentReach", "nada de la persona ni de su carpeta",
            "--sin-actualizar", "AGENTREACH_SIN_ACTUALIZAR", "no usa la red durante la revisión"]),
    ("en", ["15 days", "IP address", "the time", "program name", "reveals that this IP uses AgentReach", "nothing about the person or the folder",
            "--sin-actualizar", "AGENTREACH_SIN_ACTUALIZAR", "no network during the review"]),
])
def test_la_pantalla_de_que_hace_y_que_no_hace_lo_dice(mundo, monkeypatch, capsys, idioma, frases):
    monkeypatch.setattr(cli, "_comprobar_version_por_defecto", False)
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html", "--idioma", idioma, "--no-banner"],
             ahora=lambda: AHORA, preguntar=lambda t: "n")
    err = " ".join((capsys.readouterr().err).split())
    for frase in frases:
        assert frase in err, frase


def test_las_palabras_de_tono_siguen_neutras_en_los_textos_nuevos():
    for clave in ("intro_red", "version_nueva", "version_comando", "version_pregunta", "version_instalando", "version_instalada", "version_manual"):
        texto = cli._ERROR[clave][cli.Idioma.ES].lower()
        for palabra in (" tú ", " tu ", " usted ", " tus ", " sus "):
            assert palabra not in " " + texto + " ", (clave, palabra)


# ---- estáticas: dónde vive la red y dónde el lanzamiento de un programa ------------------------------------------------------------------


RAIZ = Path(cli.__file__).resolve().parents[1]


def _importa(arbol: ast.AST, nombres: set[str]) -> bool:
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import) and any(a.name in nombres or a.name.split(".")[0] in nombres for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and ((n.module or "") in nombres or (n.module or "").split(".")[0] in nombres):
            return True
    return False


def test_solo_un_modulo_usa_urllib_request_y_solo_la_linea_de_comandos_lo_llama():
    for archivo in RAIZ.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        if archivo.name != "actualizacion.py":
            assert not _importa(arbol, {"urllib.request", "urllib.error"}), archivo.name
        if archivo.parent.name != "cli" and archivo.name != "actualizacion.py":
            assert not _importa(arbol, {"agentreach.infra.actualizacion"}) and "actualizacion" not in [
                a.name for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) for a in n.names], archivo.name


def test_subprocess_solo_en_actualizacion_solo_run_y_nunca_con_shell():
    for archivo in RAIZ.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        if archivo.name != "actualizacion.py":
            assert not _importa(arbol, {"subprocess"}), archivo.name
            continue
        usos = [n for n in ast.walk(arbol) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess"]
        assert {u.attr for u in usos} <= {"run", "TimeoutExpired", "SubprocessError", "DEVNULL"}
        for llamada in (n for n in ast.walk(arbol) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "run"):
            shell = [k for k in llamada.keywords if k.arg == "shell"]
            assert shell and isinstance(shell[0].value, ast.Constant) and shell[0].value.value is False
            assert any(k.arg == "timeout" for k in llamada.keywords)


def test_la_revision_no_importa_el_modulo_de_red_ni_de_lanzamiento():
    for sub in ("core", "collectors", "adapters", "app", "reporting", "contracts"):
        for archivo in (RAIZ / sub).rglob("*.py"):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
            assert not _importa(arbol, {"urllib.request", "subprocess", "agentreach.infra.actualizacion"}), archivo
