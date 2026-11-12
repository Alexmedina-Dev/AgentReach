"""Historia 5: ubicaciones sensibles del usuario (~/.ssh, ~/.aws, ~/.npmrc): opt-in y solo metadatos."""

from __future__ import annotations

import builtins
import inspect
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentreach.collectors.archivos_repo import DetectorCredencialesArchivos
from agentreach.collectors.enlaces import DetectorEnlaces
from agentreach.collectors.ubicaciones_usuario import DetectorUbicacionesUsuario
from agentreach.config import Configuracion, cargar_configuracion
from agentreach.contracts import (
    Detector,
    Metadatos,
    PermisoLectura,
    PermisosArchivo,
    Proveedor,
    Ruta,
    Tipo,
)
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

CANARIO = "CANARIO-H5-AKIAIOSFAKE0123456789"
ENCENDIDO = Configuracion(incluir_ubicaciones_sensibles=True)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    h = tmp_path / "home-falso"
    (h / ".ssh").mkdir(parents=True)
    (h / ".aws").mkdir()
    (h / ".ssh" / "id_ed25519").write_text(f"-----BEGIN OPENSSH PRIVATE KEY-----\n{CANARIO}\n", encoding="utf-8")
    (h / ".ssh" / "id_ed25519.pub").write_text(f"ssh-ed25519 {CANARIO}", encoding="utf-8")
    (h / ".ssh" / "known_hosts").write_text(f"github.com ssh-ed25519 {CANARIO}", encoding="utf-8")
    (h / ".aws" / "credentials").write_text(f"[default]\naws_secret_access_key={CANARIO}\n", encoding="utf-8")
    (h / ".aws" / "config").write_text("[default]\nregion=us-east-1\n", encoding="utf-8")
    (h / ".npmrc").write_text(f"//registry.npmjs.org/:_authToken={CANARIO}\n", encoding="utf-8")
    return h


def _detector(fs, config: Configuracion, home: Path, sonda=None) -> DetectorUbicacionesUsuario:
    return DetectorUbicacionesUsuario(fs, Configuracion(
        incluir_ubicaciones_sensibles=config.incluir_ubicaciones_sensibles, home=str(home)), sonda)


def _nombres(hallazgos) -> set[str]:
    return {os.path.basename(h.ubicacion.ruta) for h in hallazgos}


class FsEspia(FsSoloLectura):
    """Cuenta cada llamada al sistema de archivos."""

    def __init__(self) -> None:
        super().__init__()
        self.llamadas: list[str] = []

    def listar(self, carpeta):
        self.llamadas.append("listar")
        return super().listar(carpeta)

    def metadatos(self, ruta):
        self.llamadas.append("metadatos")
        return super().metadatos(ruta)

    def leer_texto(self, ruta):
        self.llamadas.append("leer_texto")
        return super().leer_texto(ruta)


# (a) con el opt-in apagado no aparece nada ---------------------------------------------------------------


def test_con_el_opt_in_apagado_no_hay_hallazgos_y_no_se_toca_el_disco(home: Path):
    fs = FsEspia()
    detector = _detector(fs, Configuracion(), home)
    assert isinstance(detector, Detector)
    assert list(detector.detectar(Ruta(str(home.parent / "proyecto")))) == []
    assert fs.llamadas == []  # ni listar, ni metadatos, ni leer
    assert str(home) not in repr(detector.no_revisados) and CANARIO not in repr(detector.no_revisados)


def test_con_el_opt_in_apagado_cada_ubicacion_sale_como_no_revisada_con_su_motivo(home: Path):
    detector = _detector(FsEspia(), Configuracion(), home)
    detector.detectar(Ruta("proyecto"))
    assert sorted(n.ruta for n in detector.no_revisados) == ["~/.aws", "~/.npmrc", "~/.ssh"]
    assert {n.motivo for n in detector.no_revisados} == {MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR}


def test_el_opt_in_esta_apagado_por_defecto():
    assert Configuracion().incluir_ubicaciones_sensibles is False
    assert cargar_configuracion().incluir_ubicaciones_sensibles is False


# (b) un archivo del proyecto no puede encenderlo ----------------------------------------------------------


def test_un_archivo_de_politica_del_proyecto_no_enciende_el_opt_in(home: Path, tmp_path: Path, monkeypatch):
    proyecto = tmp_path / "proyecto"
    (proyecto / ".agentreach").mkdir(parents=True)
    for nombre in (".agentreach.toml", "agentreach.toml", ".agentreach/config.toml", "agentreach.json"):
        (proyecto / nombre).write_text("incluir_ubicaciones_sensibles = true\n", encoding="utf-8")
    monkeypatch.chdir(proyecto)  # aunque el programa se lance desde dentro del proyecto
    config = cargar_configuracion()
    assert config.incluir_ubicaciones_sensibles is False
    fs = FsEspia()
    detector = _detector(fs, config, home)
    assert list(Pipeline([detector]).ejecutar(Ruta(str(proyecto)))) == []
    assert fs.llamadas == []


def test_el_cargador_no_recibe_ninguna_ruta_de_proyecto():
    nombres = set(inspect.signature(cargar_configuracion).parameters)
    assert nombres == {"flags", "archivo_global"}


def test_solo_el_flag_o_el_archivo_global_lo_encienden(tmp_path: Path):
    assert cargar_configuracion(flags={"incluir_ubicaciones_sensibles": True}).incluir_ubicaciones_sensibles
    global_ = tmp_path / "config.toml"
    global_.write_text("incluir_ubicaciones_sensibles = true\n", encoding="utf-8")
    assert cargar_configuracion(archivo_global=str(global_)).incluir_ubicaciones_sensibles


def test_archivo_global_malo_no_enciende_y_se_informa(tmp_path: Path):
    global_ = tmp_path / "config.toml"
    global_.write_text("esto no es [toml", encoding="utf-8")
    config = cargar_configuracion(archivo_global=str(global_))
    assert config.incluir_ubicaciones_sensibles is False
    assert [n.motivo for n in config.no_revisados] == [MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE]
    ausente = cargar_configuracion(archivo_global=str(tmp_path / "no-existe.toml"))
    assert ausente.incluir_ubicaciones_sensibles is False and ausente.no_revisados == ()


def test_un_valor_que_no_es_booleano_no_enciende(tmp_path: Path):
    global_ = tmp_path / "config.toml"
    global_.write_text('incluir_ubicaciones_sensibles = "true"\n', encoding="utf-8")
    assert cargar_configuracion(archivo_global=str(global_)).incluir_ubicaciones_sensibles is False


# (c) una junction del proyecto hacia .ssh no activa la lectura ---------------------------------------------


def _junction(enlace: Path, destino: Path) -> bool:
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(destino), str(enlace))
        else:
            os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False


def test_una_junction_del_proyecto_hacia_ssh_no_activa_la_lectura(home: Path, tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    if not _junction(proyecto / "enlace-ssh", home / ".ssh"):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    fs = FsEspia()
    detectores = [
        _detector(fs, Configuracion(), home),
        DetectorCredencialesArchivos(fs),
        DetectorEnlaces(fs),
    ]
    hallazgos = Pipeline(detectores).ejecutar(Ruta(str(proyecto)))
    assert not [h for h in hallazgos if h.tipo in (Tipo.CLAVE_PRIVADA_SSH, Tipo.CREDENCIALES_DE_NUBE)]
    assert "id_ed25519" not in repr(hallazgos) and CANARIO not in repr(hallazgos)


# Con el opt-in encendido ---------------------------------------------------------------------------------------


def test_hf01_hf03_hf05_se_detectan_con_su_tipo_y_hf02_hf04_no(home: Path):
    hallazgos = list(_detector(FsSoloLectura(), ENCENDIDO, home).detectar(Ruta("proyecto")))
    por_nombre = {os.path.basename(h.ubicacion.ruta): h for h in hallazgos}
    assert set(por_nombre) == {"id_ed25519", "credentials", ".npmrc"}
    assert por_nombre["id_ed25519"].tipo is Tipo.CLAVE_PRIVADA_SSH  # HF-01
    assert por_nombre["id_ed25519"].proveedor is Proveedor.SSH
    assert por_nombre["credentials"].tipo is Tipo.CREDENCIALES_DE_NUBE  # HF-03
    assert por_nombre[".npmrc"].tipo is Tipo.CREDENCIAL_EN_ARCHIVO  # HF-05
    assert "id_ed25519.pub" not in repr(hallazgos) and "known_hosts" not in repr(hallazgos)  # HF-02
    assert not any(h.ubicacion.ruta.endswith("config") for h in hallazgos)  # HF-04


def test_un_nombre_con_forma_de_clave_privada_sin_extension_publica(home: Path):
    (home / ".ssh" / "id_rsa").write_text("x", encoding="utf-8")
    (home / ".ssh" / "deploy.pem").write_text("x", encoding="utf-8")
    (home / ".ssh" / "authorized_keys").write_text("x", encoding="utf-8")
    (home / ".ssh" / "config").write_text("Host a", encoding="utf-8")
    nombres = _nombres(_detector(FsSoloLectura(), ENCENDIDO, home).detectar(Ruta("p")))
    assert nombres == {"id_ed25519", "id_rsa", "deploy.pem", "credentials", ".npmrc"}


def test_ubicaciones_que_no_existen_no_dan_hallazgos_ni_errores(tmp_path: Path):
    vacio = tmp_path / "home-vacio"
    vacio.mkdir()
    detector = _detector(FsSoloLectura(), ENCENDIDO, vacio)
    assert list(detector.detectar(Ruta("p"))) == [] and detector.no_revisados == ()


# (d) nunca se abre el contenido -------------------------------------------------------------------------------------


def test_no_se_abre_el_contenido_de_ningun_archivo(home: Path, monkeypatch):
    raiz = os.path.normcase(str(home))

    def vigilar(original):
        def envoltura(ruta, *a, **k):
            if isinstance(ruta, (str, bytes, os.PathLike)) and os.path.normcase(os.fsdecode(ruta)).startswith(raiz):
                raise AssertionError("se abrió un archivo del home")
            return original(ruta, *a, **k)

        return envoltura

    monkeypatch.setattr(builtins, "open", vigilar(builtins.open))
    monkeypatch.setattr(io, "open", vigilar(io.open))
    monkeypatch.setattr(os, "open", vigilar(os.open))
    hallazgos = list(_detector(FsSoloLectura(), ENCENDIDO, home).detectar(Ruta("p")))
    assert len(hallazgos) == 3 and CANARIO not in repr(hallazgos)


def test_no_se_lanza_ningun_programa(home: Path, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("se intentó lanzar un programa")

    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    assert list(_detector(FsSoloLectura(), ENCENDIDO, home).detectar(Ruta("p")))


# (e) el tipo se comprueba antes de pedir tamaño o permisos ----------------------------------------------------------


class FsDeMentira:
    """Un .ssh con una tubería y un enlace, para comprobar que no se les pide tamaño ni permisos."""

    def __init__(self, home: str) -> None:
        self._h = home

    def listar(self, carpeta):
        if carpeta.endswith(".ssh"):
            return [
                Metadatos(Ruta(carpeta + "/id_tuberia"), 0, False, es_regular=False),
                Metadatos(Ruta(carpeta + "/id_enlace"), 0, False, es_enlace=True, destino_enlace=Ruta("x"), es_regular=False),
                Metadatos(Ruta(carpeta + "/id_rsa"), 10, False, es_regular=True),
            ]
        return []

    def metadatos(self, ruta):
        if ruta.endswith(".ssh") or ruta == self._h:
            return Metadatos(Ruta(ruta), 0, True)
        return None

    def leer_texto(self, ruta):
        raise AssertionError("no se lee contenido")


class SondaEspia:
    def __init__(self) -> None:
        self.pedidas: list[str] = []

    def evaluar(self, ruta):
        self.pedidas.append(os.path.basename(ruta))
        return PermisosArchivo(PermisoLectura.SI, False, False, "u", "c")

    def permiso_lectura(self, ruta):
        return self.evaluar(ruta).permiso


def test_una_tuberia_o_un_enlace_sale_no_revisado_y_no_se_les_pide_permisos(tmp_path: Path):
    sonda = SondaEspia()
    detector = DetectorUbicacionesUsuario(FsDeMentira(str(tmp_path)), Configuracion(True, str(tmp_path)), sonda)
    hallazgos = list(detector.detectar(Ruta("p")))
    assert _nombres(hallazgos) == {"id_rsa"}
    assert sonda.pedidas == ["id_rsa"]  # nunca la tubería ni el enlace
    assert sorted(os.path.basename(n.ruta) for n in detector.no_revisados) == ["id_enlace", "id_tuberia"]
    assert {n.motivo for n in detector.no_revisados} == {MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR}


def test_un_enlace_real_dentro_de_ssh_sale_no_revisado(home: Path, tmp_path: Path):
    otro = tmp_path / "otro"
    otro.mkdir()
    if not _junction(home / ".ssh" / "atajo", otro):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    detector = _detector(FsSoloLectura(), ENCENDIDO, home)
    hallazgos = list(detector.detectar(Ruta("p")))
    assert "atajo" not in repr(hallazgos)
    assert [(os.path.basename(n.ruta), n.motivo) for n in detector.no_revisados] == [
        ("atajo", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
    ]


def test_metadatos_traen_si_es_archivo_regular(tmp_path: Path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "carpeta").mkdir()
    por_nombre = {os.path.basename(m.ruta): m for m in FsSoloLectura().listar(Ruta(str(tmp_path)))}
    assert por_nombre["a.txt"].es_regular is True and por_nombre["carpeta"].es_regular is False
    assert FsSoloLectura().metadatos(Ruta(str(tmp_path / "a.txt"))).es_regular is True


# La sonda de permisos se usa solo para metadatos ----------------------------------------------------------------------


def test_los_permisos_quedan_disponibles_para_el_calculo_de_nivel(home: Path):
    sonda = SondaEspia()
    detector = _detector(FsSoloLectura(), ENCENDIDO, home, sonda)
    detector.detectar(Ruta("p"))
    assert sorted(sonda.pedidas) == [".npmrc", "credentials", "id_ed25519"]
    assert len(detector.permisos) == 3


# CLI --------------------------------------------------------------------------------------------------------------------


def test_la_cli_tiene_los_dos_flags_y_el_opt_in_apagado_por_defecto():
    from agentreach.cli import parsear_argumentos

    assert parsear_argumentos([]).incluir_ubicaciones_sensibles is False
    c = parsear_argumentos(["--incluir-ubicaciones-sensibles", "--home", "C:/x/home-falso"])
    assert c.incluir_ubicaciones_sensibles is True and c.home == "C:/x/home-falso"


def test_la_cli_sin_terminal_no_lee_nada_aunque_se_active_el_opt_in(tmp_path: Path):
    casa = tmp_path / "casa"
    casa.mkdir()
    carpeta = tmp_path / "proyecto"
    carpeta.mkdir()
    entorno = {**os.environ, "USERPROFILE": str(casa), "HOME": str(casa), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "agentreach", "--incluir-ubicaciones-sensibles"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, cwd=carpeta, env=entorno)
    assert r.returncode == 2 and "Traceback" not in r.stderr and r.stdout == ""  # el opt-in no es un permiso de lectura


# Casos del proyecto de prueba -------------------------------------------------------------------------------------------


@pytest.fixture
def home_falso() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "home-falso").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "home-falso"


def test_casos_hf_con_el_home_falso(home_falso: Path):
    apagado = _detector(FsSoloLectura(), Configuracion(), home_falso)
    assert list(apagado.detectar(Ruta("p"))) == []
    hallazgos = list(_detector(FsSoloLectura(), ENCENDIDO, home_falso).detectar(Ruta("p")))
    por_nombre = {os.path.basename(h.ubicacion.ruta): h for h in hallazgos}
    assert set(por_nombre) == {"id_ed25519", "credentials", ".npmrc"}  # HF-01, HF-03, HF-05
    assert por_nombre["id_ed25519"].tipo is Tipo.CLAVE_PRIVADA_SSH
    assert por_nombre["credentials"].tipo is Tipo.CREDENCIALES_DE_NUBE
    assert "known_hosts" not in repr(hallazgos) and ".pub" not in repr(hallazgos)  # HF-02


# Parches de la revisión ----------------------------------------------------------------------------------------------


def test_claves_con_nombre_no_estandar_tambien_se_detectan(home: Path):
    for nombre in ("github", "id_rsa.bak", "ID_RSA_trabajo"):
        (home / ".ssh" / nombre).write_text("x", encoding="utf-8")
    nombres = _nombres(_detector(FsSoloLectura(), ENCENDIDO, home).detectar(Ruta("p")))
    assert {"github", "id_rsa.bak", "ID_RSA_trabajo"} <= nombres


def test_home_que_no_existe_o_relativo_no_es_sin_hallazgos(tmp_path: Path):
    for malo in (str(tmp_path / "no-existe"), "relativo/home"):
        detector = DetectorUbicacionesUsuario(FsSoloLectura(), Configuracion(True, malo))
        assert list(detector.detectar(Ruta("p"))) == []
        assert [n.motivo for n in detector.no_revisados] == [MotivoNoRevisado.ARCHIVO_ILEGIBLE]


def test_npmrc_que_es_carpeta_se_informa(home: Path):
    (home / ".npmrc").unlink()
    (home / ".npmrc").mkdir()
    detector = _detector(FsSoloLectura(), ENCENDIDO, home)
    assert ".npmrc" not in repr(list(detector.detectar(Ruta("p"))))
    assert [os.path.basename(n.ruta) for n in detector.no_revisados] == [".npmrc"]


def test_si_falla_el_listado_de_ssh_el_resto_se_sigue_revisando(home: Path):
    class FsQueFalla(FsSoloLectura):
        def listar(self, carpeta):
            if carpeta.endswith(".ssh"):
                raise PermissionError
            return super().listar(carpeta)

    detector = _detector(FsQueFalla(), ENCENDIDO, home)
    nombres = _nombres(detector.detectar(Ruta("p")))
    assert nombres == {"credentials", ".npmrc"}
    assert [n.motivo for n in detector.no_revisados] == [MotivoNoRevisado.ARCHIVO_ILEGIBLE]


def test_una_ruta_global_relativa_nunca_activa_nada(tmp_path: Path, monkeypatch):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / "config.toml").write_text("incluir_ubicaciones_sensibles = true\n", encoding="utf-8")
    monkeypatch.chdir(proyecto)
    assert cargar_configuracion(archivo_global="config.toml").incluir_ubicaciones_sensibles is False


def test_metadatos_sin_decir_el_tipo_se_tratan_como_no_regulares():
    assert Metadatos(Ruta("a"), 1, False).es_regular is False


def test_la_cli_avisa_si_la_configuracion_global_no_se_pudo_leer(tmp_path: Path, capsys):
    """El archivo global está en la carpeta personal: se lee solo después de las dos preguntas (con «S» a la de las reglas de fuera)."""
    casa = tmp_path / "casa"
    (casa / ".agentreach").mkdir(parents=True)
    (casa / ".agentreach" / "config.toml").write_text("esto no es [toml", encoding="utf-8")
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    from agentreach import cli

    os.environ["USERPROFILE"] = os.environ["HOME"] = str(casa)  # la prueba restaura el entorno al terminar (fixture común)
    cli.main([str(proyecto), "--sin-reporte-html"])
    err = capsys.readouterr().err
    assert "no se pudo leer la configuración global" in err  # el aviso sale sin identificadores (sin --detalle)
    assert "configuracion_no_interpretable" not in err
