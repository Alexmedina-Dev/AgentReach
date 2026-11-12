"""Historia 4: credenciales en archivos (.env y similares). Se detecta por nombre y se descarta el valor."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentreach.collectors.archivos_repo import DetectorCredencialesArchivos
from agentreach.contracts import Detector, Finding, Idioma, Linea, Proveedor, Ruta, Tipo
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

CANARIO = "CANARIO-H4-sk_live_" + "9f8e7d6c5b4a39281706"


def _detectar(raiz: Path) -> list[Finding]:
    return Pipeline([DetectorCredencialesArchivos(FsSoloLectura())]).ejecutar(Ruta(str(raiz)))


def _por_archivo(hallazgos: list[Finding], nombre: str) -> list[Finding]:
    return [h for h in hallazgos if h.ubicacion.ruta.replace("\\", "/").endswith(nombre)]


def _texto_de_todo(hallazgos: list[Finding]) -> str:
    return repr(hallazgos) + "".join(str(h.a_dict(idioma)) for h in hallazgos for idioma in Idioma)


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    p = tmp_path / "proyecto"
    (p / "src").mkdir(parents=True)
    (p / ".env").write_text(
        "# comentario\n"
        f"ANTHROPIC_API_KEY={CANARIO}\n"
        f"STRIPE_SECRET_KEY={CANARIO}\n"
        f"GITHUB_TOKEN={CANARIO}\n"
        f"RAILWAY_TOKEN={CANARIO}\n"
        f"DATABASE_URL=postgres://u:{CANARIO}@db.ejemplo.com/app\n"
        f"JWT_SECRET={CANARIO}\n"
        "NODE_ENV=production\n",
        encoding="utf-8",
    )
    return p


# (a) el valor no aparece en ninguna salida ---------------------------------------------------------


def test_el_canario_no_aparece_en_ningun_objeto_ni_texto(proyecto: Path):
    hallazgos = _detectar(proyecto)
    assert hallazgos
    assert CANARIO not in _texto_de_todo(hallazgos)
    assert "sk_live" not in _texto_de_todo(hallazgos)


def test_el_canario_no_aparece_en_una_excepcion(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_bytes(b"STRIPE_SECRET_KEY=" + CANARIO.encode() + b"\x00\xff\xfe\x00")  # binario
    try:
        hallazgos = _detectar(p)
    except Exception as error:  # noqa: BLE001
        assert CANARIO not in repr(error) and CANARIO not in str(error)
    else:
        assert CANARIO not in repr(hallazgos)


# (b) línea o "línea no determinada" ---------------------------------------------------------------


def test_cada_hallazgo_trae_su_linea_correcta_o_no_determinada(proyecto: Path):
    hallazgos = _por_archivo(_detectar(proyecto), ".env")
    assert all(h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO for h in hallazgos)
    lineas = {h.proveedor: h.ubicacion.linea for h in hallazgos}
    assert lineas == {
        Proveedor.IA: 2,
        Proveedor.PAGOS: 3,
        Proveedor.CODIGO: 4,
        Proveedor.DESPLIEGUE: 5,
        Proveedor.BASE_DE_DATOS: 6,
        Proveedor.FIRMA: 7,
    }  # NODE_ENV (línea 8) no es credencial


def test_variable_repetida_da_linea_no_determinada(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text(f"API_TOKEN={CANARIO}\nAPI_TOKEN={CANARIO}\n", encoding="utf-8")
    hallazgos = _detectar(p)
    assert hallazgos and all(h.ubicacion.linea is Linea.NO_DETERMINADA for h in hallazgos)


# Falsos positivos que se omiten ---------------------------------------------------------------------


def test_plantillas_y_valores_de_relleno_se_omiten(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env.example").write_text(f"STRIPE_SECRET_KEY={CANARIO}\n", encoding="utf-8")  # PP-02
    (p / ".env").write_text(
        "API_TOKEN=changeme\nJWT_SECRET=\nDATABASE_URL=postgres://u:p@localhost/db\n"
        "AWS_KEY=AKIAIOSFODNN7EXAMPLE_SECRET\n",
        encoding="utf-8",
    )
    assert _detectar(p) == []


def test_codigo_y_referencias_no_son_hallazgo(tmp_path: Path):
    p = tmp_path / "proyecto"
    (p / ".github" / "workflows").mkdir(parents=True)
    (p / "src").mkdir()
    (p / "src" / "a.py").write_text("API_KEY = os.environ['API_KEY']\ntoken = leer()\n", encoding="utf-8")  # NO-01
    (p / ".github" / "workflows" / "deploy.yml").write_text(
        "env:\n  RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}\n", encoding="utf-8"
    )  # NO-04
    assert _detectar(p) == []


# Archivo ilegible, otros archivos, TH-17 ----------------------------------------------------------------


def test_archivo_conocido_que_no_se_puede_leer_se_reporta_por_nombre(tmp_path: Path):
    class FsIlegible(FsSoloLectura):
        def leer_texto(self, ruta):
            from agentreach.contracts import ArchivoNoLegible

            raise ArchivoNoLegible("negado")

    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env.production").write_text("X=1", encoding="utf-8")
    hallazgos = Pipeline([DetectorCredencialesArchivos(FsIlegible())]).ejecutar(Ruta(str(p)))
    assert len(hallazgos) == 1  # PP-03: existe aunque hoy no se pueda leer
    assert hallazgos[0].ubicacion.linea is Linea.NO_DETERMINADA


def test_npmrc_y_credentials_json(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".npmrc").write_text(f"registry=https://r.example.org\n//r.example.org/:_authToken={CANARIO}\n", encoding="utf-8")
    (p / "credentials.json").write_text('{\n  "type": "service_account",\n  "private_key": "' + CANARIO + '"\n}\n', encoding="utf-8")
    hallazgos = _detectar(p)
    assert [h.ubicacion.linea for h in _por_archivo(hallazgos, ".npmrc")] == [2]
    assert [h.ubicacion.linea for h in _por_archivo(hallazgos, "credentials.json")] == [3]
    assert CANARIO not in repr(hallazgos)


def test_token_de_plataforma_en_archivo_ajeno_es_th17(tmp_path: Path):
    p = tmp_path / "proyecto"
    (p / "src" / "estilos").mkdir(parents=True)
    (p / "src" / "estilos" / "notas.txt").write_text(
        f"Notas de tipografia.\nTODO borrar antes de publicar:\nRAILWAY_API_TOKEN={CANARIO}\n", encoding="utf-8"
    )
    hallazgos = _detectar(p)
    assert len(hallazgos) == 1
    h = hallazgos[0]
    assert h.tipo is Tipo.SECRETO_DE_ALTO_PODER and h.proveedor is Proveedor.DESPLIEGUE
    assert h.ubicacion.linea == 3
    assert CANARIO not in repr(hallazgos)


def test_el_detector_cumple_el_puerto():
    assert isinstance(DetectorCredencialesArchivos(FsSoloLectura()), Detector)


# Casos del proyecto de prueba -------------------------------------------------------------------------------


@pytest.fixture
def raiz_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz)


def test_casos_del_proyecto_de_prueba(raiz_prueba: Path):
    hallazgos = _detectar(raiz_prueba / "proyecto")
    env = _por_archivo(hallazgos, "proyecto/.env")
    assert {h.proveedor for h in env} == {  # PP-01a a PP-01f
        Proveedor.IA, Proveedor.PAGOS, Proveedor.CODIGO, Proveedor.DESPLIEGUE,
        Proveedor.BASE_DE_DATOS, Proveedor.FIRMA,
    }
    assert len(env) == 6
    for nombre in (".env.production", ".env.staging", ".env.local",  # PP-03, PP-04, PP-05
                   "config/servicio-rastreado.env", "config/exportacion-abierta.env"):  # GT-01, PA-01
        assert _por_archivo(hallazgos, "proyecto/" + nombre), nombre
    assert not _por_archivo(hallazgos, ".env.example")  # PP-02
    notas = _por_archivo(hallazgos, "src/estilos/notas-tipografia.txt")  # AT-08
    assert len(notas) == 1 and notas[0].tipo is Tipo.SECRETO_DE_ALTO_PODER
    assert not _por_archivo(hallazgos, "src/analizador.py")  # NO-01
    assert not [h for h in hallazgos if "proyecto-ajeno" in h.ubicacion.ruta]  # AJ-01 fuera de la raíz
    assert "sk_live" not in repr(hallazgos)


def test_aj01_solo_si_la_raiz_es_la_carpeta_contenedora(raiz_prueba: Path):
    hallazgos = _detectar(raiz_prueba)
    assert [h for h in hallazgos if "proyecto-ajeno" in h.ubicacion.ruta.replace("\\", "/")]


# Parches de la revisión ------------------------------------------------------------------------------------


def test_bom_y_saltos_de_linea_de_windows(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_bytes(("\ufeffAPI_TOKEN=" + CANARIO + "\r\nJWT_SECRET=" + CANARIO + "\r\n").encode("utf-8"))
    hallazgos = _detectar(p)
    assert sorted(h.ubicacion.linea for h in hallazgos) == [1, 2]  # el BOM no oculta la primera


def test_referencias_en_env_no_son_valores_literales(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text("API_TOKEN=${OTRA}\nJWT_SECRET=$(leer)\nDB_PASS=%CLAVE%\n", encoding="utf-8")
    assert _detectar(p) == []


def test_localhost_en_una_clave_real_no_la_descarta(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text(f"API_TOKEN=real-{CANARIO}-localhost\nDATABASE_URL=postgres://u:p@db.interno/x?h=localhost\n", encoding="utf-8")
    assert len(_detectar(p)) == 2  # solo el anfitrión local se omite, no cualquier mención


def test_repetida_da_un_solo_hallazgo_sin_linea(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text(f"API_TOKEN={CANARIO}\nAPI_TOKEN={CANARIO}\n", encoding="utf-8")
    hallazgos = _detectar(p)
    assert len(hallazgos) == 1 and hallazgos[0].ubicacion.linea is Linea.NO_DETERMINADA


def test_carpeta_git_solo_se_excluye_dentro_del_proyecto(tmp_path: Path):
    p = tmp_path / "node_modules" / ".git" / "proyecto"  # el proyecto vive bajo carpetas con esos nombres
    p.mkdir(parents=True)
    (p / ".env").write_text(f"API_TOKEN={CANARIO}\n", encoding="utf-8")
    (p / "node_modules").mkdir()
    (p / "node_modules" / ".env").write_text(f"API_TOKEN={CANARIO}\n", encoding="utf-8")
    hallazgos = _detectar(p)
    assert [h.ubicacion.ruta.replace("\\", "/").endswith("proyecto/.env") for h in hallazgos] == [True]


def test_env_demasiado_grande_se_reporta_por_nombre(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    with (p / ".env").open("wb") as f:
        f.truncate(2 * 1024 * 1024)
    hallazgos = _detectar(p)
    assert len(hallazgos) == 1 and hallazgos[0].ubicacion.linea is Linea.NO_DETERMINADA


def test_npmrc_comentado_no_se_reporta(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".npmrc").write_text(f"; //r/:_authToken={CANARIO}\n# _password={CANARIO}\n", encoding="utf-8")
    assert _detectar(p) == []
