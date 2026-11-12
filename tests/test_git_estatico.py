"""Historia 7: git sin ejecutar nada. Se lee como TEXTO la configuración de git y se reporta."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from agentreach.collectors.git_meta import SUGERENCIAS_TEXTO, DetectorGit
from agentreach.contracts import (
    ArchivoNoLegible,
    Detector,
    Finding,
    Idioma,
    Linea,
    Ruta,
    Tipo,
)
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura
from agentreach.infra.lector_config_git import (
    ConfigNoInterpretable,
    es_booleano_git,
    parsear_config,
)

CANARIO = "CANARIO-H7-ghp_" + "0123456789abcdefghijklmnopqrstuv"
TH18, TH19, TH20 = Tipo.GIT_EJECUTA_PROGRAMAS, Tipo.GIT_REMOTO_SOSPECHOSO, Tipo.GIT_NO_INTERPRETABLE


def _escribir(ruta: Path, texto: str | bytes) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(texto if isinstance(texto, bytes) else texto.encode("utf-8"))  # bytes: sin CRLF
    return ruta


def _repo(tmp: Path, config: str, **otros: str) -> Path:
    """Un proyecto con ``.git/config`` y archivos extra (``{"git/hooks/pre-commit": ...}``)."""
    p = tmp / "p"
    _escribir(p / ".git" / "config", config)
    for nombre, texto in otros.items():
        _escribir(p / nombre.replace("__", "/"), texto)
    return p


def _auditar(p: Path, fs=None) -> tuple[list[Finding], DetectorGit]:
    detector = DetectorGit(fs or FsSoloLectura(str(p)))
    return Pipeline([detector]).ejecutar(Ruta(str(p))), detector


def _tipos(hallazgos: list[Finding]) -> list[Tipo]:
    return [h.tipo for h in hallazgos]


def _lineas(hallazgos: list[Finding], tipo: Tipo) -> list[int | Linea]:
    return sorted((h.ubicacion.linea for h in hallazgos if h.tipo is tipo),
                  key=lambda n: n if isinstance(n, int) else 10**9)


def _texto(hallazgos, detector) -> str:
    return (repr(hallazgos) + repr(detector.no_revisados) + repr(detector.sugerencias)
            + "".join(str(h.a_dict(i)) for h in hallazgos for i in Idioma))


# (a) la clave de la URL no aparece en ninguna salida -------------------------------------------------------


def test_la_clave_de_la_url_no_aparece_en_ninguna_salida(tmp_path: Path):
    p = _repo(tmp_path, f'[remote "origin"]\n\turl = https://usuario:{CANARIO}@git.ejemplo.invalid/x.git\n',
              **{".gitmodules": f'[submodule "s"]\n\tpath = s\n\turl = https://u:{CANARIO}@h.invalid/s.git\n'})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH19, TH19]
    assert CANARIO not in _texto(hallazgos, detector) and "ghp_" not in _texto(hallazgos, detector)


def test_el_lector_no_deja_el_valor_en_su_representacion():
    entradas = parsear_config(f"[a]\n\tb = {CANARIO}\n")
    assert entradas[0].valor == CANARIO and CANARIO not in repr(entradas)


# (b) no se ejecuta nada ---------------------------------------------------------------------------------------


def _prohibir_programas(monkeypatch) -> None:
    def prohibido(*a, **k):
        raise AssertionError("se intentó ejecutar un programa")

    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(subprocess, "run", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    monkeypatch.setattr(os, "popen", prohibido)
    monkeypatch.setattr(os, "startfile", prohibido, raising=False)
    for familia in ("execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
                    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe"):
        monkeypatch.setattr(os, familia, prohibido, raising=False)


def test_no_se_ejecuta_ningun_programa(tmp_path: Path, monkeypatch):
    p = _repo(
        tmp_path,
        '[core]\n\tfsmonitor = python senuelo.py\n\tpager = senuelo\n[alias]\n\tx = !senuelo\n'
        '[filter "f"]\n\tclean = senuelo\n[remote "o"]\n\turl = https://u:k@h.invalid/x\n',
        **{".gitattributes": "*.dat filter=f\n", ".git__hooks__post-checkout": "#!/bin/sh\nsenuelo\n"},
    )
    _prohibir_programas(monkeypatch)
    hallazgos, _ = _auditar(p)
    assert len(hallazgos) >= 5


# (c) el lector es fiel a git ------------------------------------------------------------------------------------


def test_mayusculas_en_seccion_y_clave_se_leen_como_los_leeria_git():
    e = parsear_config("[CORE]\n\tFsMonitor = prog\n")[0]
    assert (e.seccion, e.nombre, e.valor, e.linea) == ("core", "fsmonitor", "prog", 2)


def test_subseccion_entre_comillas_respeta_mayusculas_y_escapes():
    e = parsear_config('[Remote "Or\\"igin\\\\X"]\n\tUrl = x\n')[0]
    assert (e.seccion, e.subseccion, e.nombre) == ("remote", 'Or"igin\\X', "url")


def test_la_forma_antigua_de_subseccion_va_en_minusculas():
    e = parsear_config("[remote.Origin]\n\turl = x\n")[0]
    assert (e.seccion, e.subseccion) == ("remote", "origin")


def test_comentarios_con_punto_y_coma_y_almohadilla_no_activan_nada():
    entradas = parsear_config("[core]\n; fsmonitor = prog\n# fsmonitor = otro\n\tbare = false ; fsmonitor = x\n")
    assert [(e.nombre, e.valor) for e in entradas] == [("bare", "false")]


def test_un_fsmonitor_despues_de_un_comentario_falso_se_lee():
    entradas = parsear_config("[core]\n; [core] fsmonitor = comentario\n#\tfsmonitor = otro\n\tfsmonitor = real\n")
    assert [(e.nombre, e.valor, e.linea) for e in entradas] == [("fsmonitor", "real", 4)]


def test_valores_con_barra_invertida_y_linea_continuada():
    entradas = parsear_config('[core]\n\tpager = python \\\n"C:/x/senuelo.py"\n\tbare = a\\\\b\\tc\\"d\n')
    assert entradas[0].valor == "python C:/x/senuelo.py" and entradas[0].linea == 2
    assert entradas[1].valor == 'a\\b\tc"d' and entradas[1].linea == 4


def test_la_almohadilla_dentro_de_comillas_es_parte_del_valor():
    e = parsear_config('[core]\n\tpager = "less # no es comentario" ; si lo es\n')[0]
    assert e.valor == "less # no es comentario"


def test_variable_en_la_misma_linea_que_el_encabezado_y_clave_sin_igual():
    entradas = parsear_config("[core] fsmonitor = prog\n[x]\n\tflag\n")
    assert [(e.nombre, e.valor) for e in entradas] == [("fsmonitor", "prog"), ("flag", None)]


def test_marca_bom_y_fin_de_linea_windows():
    entradas = parsear_config("\ufeff[core]\r\n\tfsmonitor = prog\r\n")
    assert entradas[0].valor == "prog" and entradas[0].linea == 2


@pytest.mark.parametrize("texto", [
    '[core\n\tx = 1\n', '[core]\n\tx = "TEXTO-DEL-ARCHIVO\n', "[core]\n\t= valor\n", "[core]\n\tx = a\\qb\n",
    "x = 1\n", '[core "sub]\n', "[core]\n\t1x = 2\n",
])
def test_texto_que_git_rechazaria_no_se_interpreta(texto):
    with pytest.raises(ConfigNoInterpretable) as info:
        parsear_config(texto)
    assert "TEXTO-DEL-ARCHIVO" not in str(info.value)  # el mensaje nunca copia el texto


@pytest.mark.parametrize("valor,esperado", [
    ("true", True), ("YES", True), ("on", True), ("1", True), ("2", True), (None, True),
    ("false", False), ("No", False), ("off", False), ("0", False), ("", False),
    ("python x.py", None), ("senuelo", None), ("truee", None),
])
def test_booleanos_de_git(valor, esperado):
    assert es_booleano_git(valor) is esperado


# (d) un ciclo de include termina ------------------------------------------------------------------------------------


def test_un_ciclo_de_include_termina_y_el_programa_del_include_se_reporta(tmp_path: Path):
    p = _repo(tmp_path, "[include]\n\tpath = a.config\n",
              **{".git__a.config": "[include]\n\tpath = b.config\n[core]\n\tfsmonitor = prog\n",
                 ".git__b.config": "[include]\n\tpath = a.config\n"})
    hallazgos, detector = _auditar(p)
    assert TH18 in _tipos(hallazgos) and TH20 in _tipos(hallazgos)  # el ciclo no tapa el programa
    assert MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA in {n.motivo for n in detector.no_revisados}


def test_un_include_que_apunta_a_si_mismo_termina(tmp_path: Path):
    p = _repo(tmp_path, "[include]\n\tpath = config\n")
    hallazgos, _ = _auditar(p)
    assert TH20 in _tipos(hallazgos)


def test_un_include_que_no_existe_se_ignora_como_hace_git(tmp_path: Path):
    p = _repo(tmp_path, "[include]\n\tpath = no-existe.config\n[includeIf \"gitdir:/x/\"]\n\tpath = tampoco\n")
    hallazgos, detector = _auditar(p)
    assert hallazgos == [] and [n.motivo for n in detector.no_revisados] == [MotivoNoRevisado.HISTORIAL_GIT_FASE2]


def test_la_cadena_de_include_se_corta_a_profundidad_10(tmp_path: Path):
    p = _repo(tmp_path, "[include]\n\tpath = c1.config\n")
    for i in range(1, 13):
        _escribir(p / ".git" / f"c{i}.config", f"[include]\n\tpath = c{i + 1}.config\n")
    hallazgos, detector = _auditar(p)
    assert TH20 in _tipos(hallazgos)
    assert MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA in {n.motivo for n in detector.no_revisados}


def test_includeif_tambien_se_sigue(tmp_path: Path):
    p = _repo(tmp_path, '[includeIf "gitdir:~/trabajo/"]\n\tpath = extra.config\n',
              **{".git__extra.config": "[core]\n\tsshCommand = ssh -o ProxyCommand=senuelo\n"})
    assert _tipos(_auditar(p)[0]) == [TH18]


# (e) un .git/config ilegible da TH-20, no una excepción -------------------------------------------------------------


def test_config_con_sintaxis_que_el_lector_no_entiende_da_th20_y_no_revisado(tmp_path: Path):
    p = _repo(tmp_path, "[core\n\tfsmonitor = prog\n")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20]
    assert MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE in {n.motivo for n in detector.no_revisados}


# (g0) límites duros: solo leer_seguro ---------------------------------------------------------------------------------


def _motivos(detector: DetectorGit) -> set[MotivoNoRevisado]:
    return {n.motivo for n in detector.no_revisados}


def test_config_de_5_mb_mas_un_byte_da_th20_y_demasiado_grande(tmp_path: Path):
    p = tmp_path / "p"
    (p / ".git").mkdir(parents=True)
    with (p / ".git" / "config").open("wb") as f:
        f.truncate(5 * 1024 * 1024 + 1)
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE in _motivos(detector)


def test_config_con_bytes_que_no_son_utf8_da_th20(tmp_path: Path):
    p = _repo(tmp_path, b"[core]\n\tpager = \xff\xfe\xfd\n")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.CODIFICACION_NO_UTF8 in _motivos(detector)


class FsConConfigRara(FsSoloLectura):
    """Simula que ``.git/config`` es una tubería: leer lanza el motivo ``no_es_archivo_regular``."""

    def leer_texto(self, ruta):
        if ruta.replace("\\", "/").endswith(".git/config"):
            raise ArchivoNoLegible("tuberia", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
        return super().leer_texto(ruta)


def test_config_que_es_una_tuberia_simulada_da_th20(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n\tfsmonitor = prog\n")
    hallazgos, detector = _auditar(p, FsConConfigRara(str(p)))
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR in _motivos(detector)


def test_config_que_es_un_enlace_da_th20(tmp_path: Path):
    p = tmp_path / "p"
    (p / ".git").mkdir(parents=True)
    destino = _escribir(tmp_path / "otro" / "config", "[core]\n\tfsmonitor = prog\n")
    try:
        os.symlink(destino, p / ".git" / "config")
    except (OSError, NotImplementedError):
        pytest.skip("el entorno no permite crear enlaces simbólicos")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR in _motivos(detector)


def test_los_hooks_solo_se_listan_no_se_abre_ninguno(tmp_path: Path):
    leidos: list[str] = []

    class FsEspia(FsSoloLectura):
        def leer_texto(self, ruta):
            leidos.append(ruta.replace("\\", "/"))
            return super().leer_texto(ruta)

    p = _repo(tmp_path, "[core]\n", **{".git__hooks__post-checkout": "#!/bin/sh\n", ".git__hooks__pre-commit.sample": "x"})
    hallazgos, _ = _auditar(p, FsEspia(str(p)))
    assert [os.path.basename(h.ubicacion.ruta) for h in hallazgos] == ["post-checkout"]  # el .sample no
    assert not [r for r in leidos if "/hooks/" in r]


# (f) cada clave de (b) tiene su caso ------------------------------------------------------------------------------------


CLAVES_QUE_EJECUTAN = [
    ("core.fsmonitor", "[core]\n\tfsmonitor = python senuelo.py\n"),
    ("core.hooksPath", "[core]\n\thooksPath = .husky\n"),
    ("filter.clean", '[filter "f"]\n\tclean = senuelo clean\n'),
    ("filter.smudge", '[filter "f"]\n\tsmudge = senuelo smudge\n'),
    ("filter.process", '[filter "f"]\n\tprocess = senuelo\n'),
    ("alias !", "[alias]\n\tpublicar = !senuelo\n"),
    ("core.sshCommand", "[core]\n\tsshCommand = ssh -o ProxyCommand=senuelo\n"),
    ("core.pager", "[core]\n\tpager = senuelo\n"),
    ("diff.external", "[diff]\n\texternal = senuelo\n"),
    ("gpg.program", "[gpg]\n\tprogram = senuelo\n"),
    ("gpg.ssh.program", '[gpg "ssh"]\n\tprogram = senuelo\n'),
    ("core.editor", "[core]\n\teditor = senuelo\n"),
    ("core.askPass", "[core]\n\taskPass = senuelo\n"),
    ("sequence.editor", "[sequence]\n\teditor = senuelo\n"),
    ("diff.driver.textconv", '[diff "d"]\n\ttextconv = senuelo\n'),
    ("diff.driver.command", '[diff "d"]\n\tcommand = senuelo\n'),
    ("merge.driver", '[merge "m"]\n\tdriver = senuelo %O %A %B\n'),
    ("mergetool.cmd", '[mergetool "t"]\n\tcmd = senuelo\n'),
    ("difftool.cmd", '[difftool "t"]\n\tcmd = senuelo\n'),
    ("remote.uploadpack", '[remote "o"]\n\tuploadpack = senuelo\n'),
    ("pager.log", "[pager]\n\tlog = senuelo\n"),
    ("credential.helper !", "[credential]\n\thelper = !senuelo\n"),
    ("submodule.update !", '[submodule "s"]\n\tupdate = !senuelo\n'),
    ("browser.cmd", '[browser "b"]\n\tcmd = senuelo\n'),
    ("man.cmd", '[man "m"]\n\tcmd = senuelo\n'),
    ("trailer.cmd", '[trailer "t"]\n\tcmd = senuelo\n'),
    ("remote.vcs", '[remote "o"]\n\tvcs = senuelo\n'),
    ("uploadpack.packObjectsHook", "[uploadpack]\n\tpackObjectsHook = senuelo\n"),
    ("web.browser", "[web]\n\tbrowser = senuelo\n"),
    ("credential.helper ruta", '[credential "https://h.invalid"]\n\thelper = /usr/bin/senuelo\n'),
]


@pytest.mark.parametrize("clave,config", CLAVES_QUE_EJECUTAN, ids=[c for c, _ in CLAVES_QUE_EJECUTAN])
def test_cada_clave_que_ejecuta_un_programa_se_detecta_con_su_linea(tmp_path: Path, clave, config):
    hallazgos, _ = _auditar(_repo(tmp_path, config))
    assert _tipos(hallazgos) == [TH18], clave
    assert hallazgos[0].ubicacion.linea == 2 and hallazgos[0].ubicacion.ruta.replace("\\", "/").endswith(".git/config")


@pytest.mark.parametrize("config", [
    "[core]\n\tfsmonitor = true\n", "[core]\n\tfsmonitor = false\n", "[core]\n\tfsmonitor = yes\n",
    "[core]\n\tfsmonitor = no\n", "[core]\n\tfsmonitor = 0\n", "[core]\n\tfsmonitor =\n", "[core]\n\tfsmonitor\n",
    "[core]\n\tpager = \n", "[core]\n\thooksPath =\n",
    "[alias]\n\tst = status -s\n", "[credential]\n\thelper = manager\n", "[credential]\n\thelper = cache\n",
    "[pager]\n\tlog = false\n", "[user]\n\tname = Persona\n\temail = a@b.invalid\n",
    "[core]\n\trepositoryformatversion = 0\n\tfilemode = false\n\tbare = false\n",
    '[filter "lfs"]\n\trequired = true\n',  # sin comando local
], ids=lambda c: c.strip().replace("\n", "|").replace("\t", "")[:40])
def test_los_controles_no_se_reportan(tmp_path: Path, config):
    assert _auditar(_repo(tmp_path, config))[0] == []


def test_filtro_lfs_en_gitattributes_sin_comando_local_no_se_reporta(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitattributes": "*.bin filter=lfs diff=lfs merge=lfs -text\n"})
    assert _auditar(p)[0] == []


def test_filtro_con_comando_nombrado_en_gitattributes_se_reporta_en_la_config(tmp_path: Path):
    p = _repo(tmp_path, '[filter "senuelo"]\n\tclean = senuelo\n\tsmudge = senuelo\n',
              **{".gitattributes": "*.dat filter=senuelo\n"})
    hallazgos, _ = _auditar(p)
    assert _tipos(hallazgos) == [TH18, TH18] and _lineas(hallazgos, TH18) == [2, 3]


def test_gitattributes_que_no_se_puede_leer_se_informa(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitattributes": b"*.bin filter=\xff\xfe\n"})
    _, detector = _auditar(p)
    assert MotivoNoRevisado.CODIFICACION_NO_UTF8 in _motivos(detector)


def test_un_entero_desmesurado_en_fsmonitor_no_tumba_la_auditoria(tmp_path: Path):
    hallazgos, _ = _auditar(_repo(tmp_path, "[core]\n\tfsmonitor = " + "9" * 5000 + "\n"))
    assert _tipos(hallazgos) == [TH18]  # no es un booleano que git acepte: se trata como programa


def test_un_include_con_tilde_no_da_th20_ni_copia_texto_del_archivo(tmp_path: Path):
    p = _repo(tmp_path, '[includeIf "gitdir:~/trabajo/"]\n\tpath = ~/.gitconfig-trabajo-SECRETO\n')
    hallazgos, detector = _auditar(p)
    assert hallazgos == []  # git lo seguiría con la carpeta personal; aquí solo se informa
    assert "SECRETO" not in repr(detector.no_revisados)
    assert MotivoNoRevisado.ARCHIVO_ILEGIBLE in _motivos(detector)


def test_un_include_alcanzado_por_dos_caminos_no_duplica_hallazgos(tmp_path: Path):
    p = _repo(tmp_path, "[include]\n\tpath = a.config\n\tpath = b.config\n",
              **{".git__a.config": "[include]\n\tpath = comun.config\n",
                 ".git__b.config": "[include]\n\tpath = comun.config\n",
                 ".git__comun.config": "[core]\n\tpager = senuelo\n"})
    assert _tipos(_auditar(p)[0]) == [TH18]


def test_gitmodules_solo_se_evalua_como_lo_lee_git(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitmodules": '[core]\n\tfsmonitor = senuelo\n[alias]\n\tx = !senuelo\n'
                                                       '[submodule "a"]\n\tpath = a\n\turl = https://github.com/o/r\n'})
    assert _auditar(p)[0] == []  # git ignora esas claves en .gitmodules


def test_gitmodules_ilegible_da_th20(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitmodules": b"[submodule \"a\"\n\turl = x\n"})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE in _motivos(detector)


def test_gitattributes_ilegible_da_th20(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitattributes": b"*.bin filter=\xff\xfe\n"})
    assert _tipos(_auditar(p)[0]) == [TH20]


def test_un_hook_enlazado_se_reporta_y_se_informa(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n")
    (p / ".git" / "hooks").mkdir()
    destino = _escribir(tmp_path / "otro" / "malo.sh", "x")
    try:
        os.symlink(destino, p / ".git" / "hooks" / "pre-commit")
    except (OSError, NotImplementedError):
        pytest.skip("el entorno no permite crear enlaces simbólicos")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH18] and MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR in _motivos(detector)


def test_credencial_en_el_nombre_de_una_regla_insteadof(tmp_path: Path):
    p = _repo(tmp_path, '[url "https://u:k@h.invalid/"]\n\tinsteadOf = https://h.invalid/\n')
    assert _tipos(_auditar(p)[0]) == [TH19]


def test_los_hooks_sin_sample_se_reportan_y_los_sample_no(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".git__hooks__pre-push": "x", ".git__hooks__commit-msg.sample": "x"})
    hallazgos, _ = _auditar(p)
    assert [(h.tipo, os.path.basename(h.ubicacion.ruta)) for h in hallazgos] == [(TH18, "pre-push")]


# URLs de remotos y submódulos ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("url", [
    "https://usuario:clave@git.ejemplo.invalid/x.git",  # GT-03: usuario y clave
    "https://usuario:TOKEN@git.ejemplo.invalid/x.git",  # GT-08: valor de relleno, igual se reporta
    "https://ghp_" + "0123456789abcdefghijklmnopqrstuvwxyz@github.com/o/r.git",  # token como usuario
    "https://0123456789abcdef0123456789abcdef@h.invalid/o/r.git",  # token largo sin prefijo conocido
    "ext::sh -c senuelo",
    "-oProxyCommand=senuelo",
    "https://h.invalid/x.git\\nsegunda",
])
def test_urls_con_credencial_o_direccion_sospechosa_se_reportan_en_remotos(tmp_path: Path, url):
    hallazgos, _ = _auditar(_repo(tmp_path, f'[remote "origin"]\n\turl = {url}\n'))
    assert _tipos(hallazgos) == [TH19] and hallazgos[0].ubicacion.linea == 2


@pytest.mark.parametrize("url", [
    "https://github.com/o/r.git", "git@github.com:o/r.git", "ssh://git@h.invalid/o/r.git",
    "https://usuario@h.invalid/o/r.git", "../otro.git", "C:/repos/otro",
])
def test_urls_normales_no_se_reportan(tmp_path: Path, url):
    assert _auditar(_repo(tmp_path, f'[remote "origin"]\n\turl = {url}\n'))[0] == []


def test_submodulo_con_direccion_sospechosa(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n", **{".gitmodules": '[submodule "a"]\n\tpath = a\n\turl = ext::sh -c x\n'
                                                      '[submodule "b"]\n\tpath = b\n\turl = ../../../x\n'
                                                      '[submodule "c"]\n\tpath = c\n\turl = https://github.com/o/r\n'})
    hallazgos, _ = _auditar(p)
    assert _tipos(hallazgos) == [TH19, TH19] and _lineas(hallazgos, TH19) == [3, 6]
    assert all(h.ubicacion.ruta.replace("\\", "/").endswith(".gitmodules") for h in hallazgos)


def test_url_de_submodulo_en_el_git_config_tambien_se_revisa(tmp_path: Path):
    p = _repo(tmp_path, '[submodule "a"]\n\turl = https://u:k@h.invalid/a.git\n')
    assert _tipos(_auditar(p)[0]) == [TH19]


# (g) wincred ---------------------------------------------------------------------------------------------------------------------------


def test_wincred_sugiere_otro_ayudante_de_credenciales_solo_como_texto(tmp_path: Path):
    p = _repo(tmp_path, "[credential]\n\thelper = wincred\n")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH18]
    claves = set(detector.sugerencias.values())
    assert claves == {"cambiar_ayudante_wincred"}
    for idioma in Idioma:
        assert "wincred" in SUGERENCIAS_TEXTO["cambiar_ayudante_wincred"][idioma].lower()


def test_otros_ayudantes_no_dan_sugerencia(tmp_path: Path):
    _, detector = _auditar(_repo(tmp_path, "[credential]\n\thelper = manager\n"))
    assert detector.sugerencias == {}


# historial, .git raro, sin .git --------------------------------------------------------------------------------------------------------------


def test_el_historial_sale_como_no_revisado_sin_hallazgo(tmp_path: Path):
    hallazgos, detector = _auditar(_repo(tmp_path, "[core]\n"))
    assert hallazgos == []
    assert [n.motivo for n in detector.no_revisados] == [MotivoNoRevisado.HISTORIAL_GIT_FASE2]  # GT-02


def test_sin_carpeta_git_no_hay_nada_que_decir(tmp_path: Path):
    p = tmp_path / "p"
    p.mkdir()
    hallazgos, detector = _auditar(p)
    assert hallazgos == [] and detector.no_revisados == ()


def test_git_que_es_un_archivo_no_se_interpreta_en_el_mvp_y_se_reporta_como_th20(tmp_path: Path):
    p = tmp_path / "p"
    _escribir(p / ".git", "gitdir: ../real/.git\n")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE in _motivos(detector)


def test_el_resultado_anterior_no_se_arrastra(tmp_path: Path):
    p = _repo(tmp_path, "[core]\n\tfsmonitor = prog\n")
    detector = DetectorGit(FsSoloLectura(str(p)))
    assert len(list(detector.detectar(Ruta(str(p))))) == 1
    (p / ".git" / "config").write_bytes(b"[core]\n")
    assert list(detector.detectar(Ruta(str(p)))) == []


def test_el_detector_cumple_el_puerto():
    assert isinstance(DetectorGit(FsSoloLectura()), Detector)


def test_una_carpeta_git_que_es_un_enlace_se_informa(tmp_path: Path):
    p = tmp_path / "p"
    real = tmp_path / "real-git"
    real.mkdir()
    p.mkdir()
    try:
        os.symlink(real, p / ".git", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("el entorno no permite crear enlaces simbólicos")
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH20] and MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR in _motivos(detector)


# Casos del proyecto de prueba -----------------------------------------------------------------------------------------------------------------------


@pytest.fixture
def raiz_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "trampas-git").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz)


@pytest.mark.parametrize("caso,esperado", [
    ("fsmonitor-malo", [TH18]),  # GT-04
    ("hookspath-dentro", [TH18]),  # GT-05
    ("filtro-gitattributes", [TH18, TH18]),  # GT-06 (clean y smudge)
    ("hook-ejecutable", [TH18]),  # GT-07 (el .sample no)
    ("remoto-relleno", [TH19]),  # GT-08
    ("config-formato-retorcido", [TH18]),  # GT-09
    ("ssh-command", [TH18]),  # GT-14
    ("pager", [TH18]),  # GT-15
    ("alias-shell", [TH18]),  # GT-16
    ("diff-external", [TH18]),  # GT-17
    ("gpg-program", [TH18]),  # GT-18
    ("fsmonitor-true", []),  # GT-10 (control)
    ("fsmonitor-false", []),  # GT-11 (control)
    ("filtro-lfs", []),  # GT-12 (control)
])
def test_casos_gt_del_proyecto_de_prueba(raiz_prueba: Path, caso, esperado):
    p = raiz_prueba / "trampas-git" / caso
    hallazgos, detector = _auditar(p)
    assert sorted(t.value for t in _tipos(hallazgos)) == sorted(t.value for t in esperado), caso
    assert [n.motivo for n in detector.no_revisados if n.motivo is MotivoNoRevisado.HISTORIAL_GIT_FASE2]


def test_gt13_el_ciclo_termina_sin_colgarse_y_sin_ejecutar(raiz_prueba: Path, monkeypatch):
    _prohibir_programas(monkeypatch)
    hallazgos, detector = _auditar(raiz_prueba / "trampas-git" / "config-retorcida-ciclo")
    assert TH20 in _tipos(hallazgos) or TH18 in _tipos(hallazgos)
    assert MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA in _motivos(detector)


def test_gt03_remoto_con_credencial_del_proyecto_y_gt02_historial(raiz_prueba: Path):
    p = raiz_prueba / "proyecto"
    hallazgos, detector = _auditar(p)
    assert TH19 in _tipos(hallazgos) and "ghp_" not in _texto(hallazgos, detector)
    assert MotivoNoRevisado.HISTORIAL_GIT_FASE2 in _motivos(detector)  # GT-02: no hay hallazgo


def test_tr01_nada_se_ejecuta_y_pwned_no_existe(raiz_prueba: Path, monkeypatch):
    _prohibir_programas(monkeypatch)
    for caso in (raiz_prueba / "trampas-git").iterdir():
        _auditar(caso)
    _auditar(raiz_prueba / "proyecto")
    assert not (raiz_prueba / "trampas" / "PWNED.txt").exists()


def test_no05_los_sample_no_generan_candidato(raiz_prueba: Path):
    hallazgos, _ = _auditar(raiz_prueba / "trampas-git" / "hook-ejecutable")
    assert not [h for h in hallazgos if h.ubicacion.ruta.endswith(".sample")]
