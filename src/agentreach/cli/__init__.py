"""Interfaz de línea de comandos (argparse): ``agentreach audit RUTA`` (o el atajo ``agentreach RUTA``) y ``agentreach doctor``.

Códigos de salida: 0 sin hallazgos comprobados; 1 con alguno (con ``--estricto``, también con entradas no revisadas);
2 si no se pudo empezar (carpeta inválida, argumentos mal, ``--salida`` dentro del proyecto); 3 error interno inesperado
(no se muestra un reporte parcial). El código sale de la lista corregida por la autocomprobación, no del texto impreso.
``doctor`` sale 0 sin fallos y 1 con alguno. El banner de marca solo sale en una terminal interactiva (Historia 13c).
"""

import argparse
import dataclasses
import errno
import os
import re
import shutil
import sys
from collections.abc import Callable
from datetime import datetime
from importlib import metadata

from agentreach.app.auditar import auditar
from agentreach.app.doctor import Entorno
from agentreach.app.doctor import codigo_de_salida as codigo_doctor
from agentreach.app.doctor import comprobar as comprobar_entorno
from agentreach.app.doctor import formatear as formatear_doctor
from agentreach.cli.reportes import dentro as _dentro
from agentreach.cli.reportes import escribir_reporte, guardar_preferencia, leer_preferencia
from agentreach.config import Configuracion, archivo_global_por_defecto, cargar_configuracion
from agentreach.contracts import Idioma, Plataforma
from agentreach.core.catalogo_explicaciones import TITULO_MOTIVO, Tono
from agentreach.infra.navegador import abrir as abrir_navegador
from agentreach.reporting.formato import (
    Color,
    activar_vt,
    ajustar,
    ancho_de_trabajo,
    decidir_color,
    preparar_salida,
    resolver_tema,
    resolver_tema_marca,
)
from agentreach.reporting.gate import preparar
from agentreach.reporting.html import ReporteDemasiadoGrande, generar_html
from agentreach.reporting.limpieza import escribir_peligrosos
from agentreach.reporting.marca import Tamano, banner, debe_mostrarse, tamano_efectivo
from agentreach.reporting.texto import generar

# Historia 28: permiso de segundo nivel, aparte de la primera pregunta: las reglas de los agentes FUERA del proyecto
_PREGUNTA_REGLAS = {
    (Idioma.ES, Tono.CERCANO): ("AgentReach necesita ver las reglas de tus agentes en tu carpeta personal (solo las reglas, nunca los valores). "
                                "Sin ellas no puede decidir bien los niveles. ¿Se permite? (S/N) "),
    (Idioma.ES, Tono.FORMAL): ("AgentReach necesita ver las reglas de sus agentes en su carpeta personal (solo las reglas, nunca los valores). "
                               "Sin ellas no puede decidir bien los niveles. ¿Se permite? (S/N) "),
    (Idioma.EN, Tono.CERCANO): ("AgentReach needs to see the rules of your agents in your home folder (only the rules, never the values). "
                                "Without them it cannot decide the levels properly. Is this allowed? (Y/N) "),
    (Idioma.EN, Tono.FORMAL): ("AgentReach needs to see the rules of your agents in your home folder (only the rules, never the values). "
                               "Without them it cannot decide the levels properly. Is this allowed? (Y/N) "),
}
_ESPACIO_ANTES = ("", "", "")  # decisión de Alex: el banner necesita aire, tres líneas en blanco antes
_ESPACIO_DESPUES = ("", "")  # y tres después (la cuarta la añade el formateador entre el banner y el texto)

_ERROR = {
    "carpeta": {
        Idioma.ES: "error: la carpeta indicada no existe o no es una carpeta",
        Idioma.EN: "error: the folder does not exist or is not a folder"},
    "salida": {
        Idioma.ES: "error: --salida no puede escribir dentro de la carpeta auditada (AgentReach no cambia nada ahí)",
        Idioma.EN: "error: --salida cannot write inside the audited folder (AgentReach changes nothing there)"},
    "salida_existe": {
        Idioma.ES: "error: el archivo de --salida ya existe y AgentReach no pisa archivos; hay que elegir otro nombre o borrarlo antes",
        Idioma.EN: "error: the --salida file already exists and AgentReach does not overwrite files; pick another name or delete it first"},
    "cancelado_ctrl_c": {Idioma.ES: "Cancelado por la persona (Ctrl+C).", Idioma.EN: "Cancelled by the person (Ctrl+C)."},
    "ruta_real": {Idioma.ES: "(ruta real: {real})", Idioma.EN: "(real path: {real})"},
    "tipo_contiene_home": {Idioma.ES: "una carpeta que contiene la carpeta personal", Idioma.EN: "a folder that contains the home folder"},
    "escritura": {
        Idioma.ES: "error: no se pudo escribir el archivo de --salida", Idioma.EN: "error: could not write the --salida file"},
    "interno": {
        Idioma.ES: "Error interno de AgentReach; no se muestra un reporte parcial",
        Idioma.EN: "AgentReach internal error; no partial report is shown"},
    "sin_terminal": {
        Idioma.ES: "error: AgentReach es una herramienta de terminal que opera una persona: sin una terminal interactiva no lee nada",
        Idioma.EN: "error: AgentReach is a terminal tool operated by a person: without an interactive terminal it reads nothing"},
    "intro_que": {
        Idioma.ES: "AgentReach audita, en solo lectura, a qué puede acceder un agente de IA en una carpeta.",
        Idioma.EN: "AgentReach audits, read-only, what an AI agent can reach in a folder."},
    "intro_hace": {
        Idioma.ES: ("Qué hace: recorre los archivos de la carpeta y la configuración de los agentes, e informa qué podría alcanzar "
                    "un agente, con evidencia y nivel de confianza."),
        Idioma.EN: ("What it does: it walks the folder's files and the agents' configuration, and reports what an agent could reach, "
                    "with evidence and a confidence level.")},
    "intro_no_hace": {
        Idioma.ES: ("Qué no hace: no cambia nada del proyecto, no usa la red, no ejecuta los programas del proyecto y no muestra valores de "
                    "secretos. Solo guarda el reporte fuera de la carpeta revisada, y solo abre el navegador con permiso."),
        Idioma.EN: ("What it does not do: it changes nothing in the project, uses no network, runs none of the project's programs and shows "
                    "no secret values. It only saves the report outside the reviewed folder, and only opens the browser with permission.")},
    "pregunta_leer": {
        Idioma.ES: "¿Se permite que AgentReach lea esta carpeta?\n  {ruta}\n{aviso}(S/N) ",
        Idioma.EN: "Is AgentReach allowed to read this folder?\n  {ruta}\n{aviso}(Y/N) "},
    "aviso_riesgosa": {
        Idioma.ES: "ATENCIÓN: es {tipo}; puede tardar y mirar muchos archivos.\n",
        Idioma.EN: "WARNING: it is {tipo}; it may take long and look at many files.\n"},
        "json": {
        Idioma.ES: "error: --json todavía no existe en esta versión",
        Idioma.EN: "error: --json does not exist in this version yet"},
    "html_sin_salida": {
        Idioma.ES: "error: --formato html necesita --salida ARCHIVO (un HTML no se imprime en la terminal)",
        Idioma.EN: "error: --formato html needs --salida FILE (an HTML is not printed to the terminal)"},
    "reporte_donde": {
        Idioma.ES: "Reporte HTML guardado en: {ruta}",
        Idioma.EN: "HTML report saved at: {ruta}"},
    "reporte_que": {
        Idioma.ES: "Al abrirlo en el navegador se ve: el resumen por nivel, la lista de hallazgos y la tabla.",
        Idioma.EN: "Opened in the browser it shows: the summary by level, the list of findings and the table."},
    "reporte_no": {
        Idioma.ES: "aviso: no se creó el reporte HTML ({motivo})",
        Idioma.EN: "warning: the HTML report was not created ({motivo})"},
    "motivo_sin_home": {Idioma.ES: "no hay una carpeta personal utilizable", Idioma.EN: "there is no usable home folder"},
    "motivo_dentro": {
        Idioma.ES: "la carpeta de reportes quedaría dentro de la carpeta revisada y AgentReach no escribe ahí; con --salida se elige una ruta de fuera",
        Idioma.EN: "the reports folder would fall inside the reviewed folder and AgentReach writes nothing there; --salida picks a path outside"},
    "motivo_enlace": {
        Idioma.ES: "AgentReach-reportes es un enlace y no se escribe a través de enlaces",
        Idioma.EN: "AgentReach-reportes is a link and nothing is written through links"},
    "motivo_escritura": {Idioma.ES: "no se pudo escribir el archivo", Idioma.EN: "the file could not be written"},
    "motivo_demasiado_grande": {Idioma.ES: "el reporte pasa de los topes de tamaño", Idioma.EN: "the report exceeds the size limits"},
    "pregunta_abrir": {Idioma.ES: "¿Abrir el reporte en el navegador? (S/N) ", Idioma.EN: "Open the report in the browser? (Y/N) "},
    "solo_sn": {Idioma.ES: "Solo se acepta S o N (sin Enter por defecto).", Idioma.EN: "Only Y or N is accepted (no default on Enter)."},
    "sin_respuesta_reglas": {
        Idioma.ES: "Sin una respuesta válida (solo S o N) después de {n} intentos: no se leerá nada fuera del proyecto.",
        Idioma.EN: "No valid answer (only Y or N) after {n} tries: nothing outside the project will be read."},
    "sin_reglas": {
        Idioma.ES: "No se leerá nada fuera del proyecto: los niveles que dependen de las reglas quedan en «potencial».",
        Idioma.EN: "Nothing outside the project will be read: the levels that depend on the rules stay at \"potential\"."},
    "no_leyo": {Idioma.ES: "No se leyó nada.", Idioma.EN: "Nothing was read."},
    "sin_respuesta_carpeta": {
        Idioma.ES: "Sin una respuesta válida (solo S o N) después de {n} intentos: no se revisó nada.",
        Idioma.EN: "No valid answer (only Y or N) after {n} tries: nothing was reviewed."},
    "sin_respuesta_abrir": {
        Idioma.ES: "Sin una respuesta válida (solo S o N) después de {n} intentos: no se abrió el reporte ni se recordó nada.",
        Idioma.EN: "No valid answer (only Y or N) after {n} tries: the report was not opened and nothing was remembered."},
    "respuesta_guardada": {
        Idioma.ES: "(Respuesta recordada en {ruta}; si ese archivo se borra, volverá a preguntar. También sirven --abrir y --no-abrir.)",
        Idioma.EN: "(Answer remembered in {ruta}; if that file is deleted, it will ask again. --abrir and --no-abrir also work.)"},
    "no_abrio": {
        Idioma.ES: "aviso: no se pudo abrir el navegador; el archivo se puede abrir a mano.",
        Idioma.EN: "warning: the browser could not be opened; the file can be opened by hand."},
    "tipo_home": {Idioma.ES: "la carpeta personal", Idioma.EN: "the home folder"},
    "tipo_raiz": {Idioma.ES: "la raíz de un disco", Idioma.EN: "the root of a drive"},
    "argumentos": {Idioma.ES: "error en los argumentos", Idioma.EN: "argument error"},
    "aviso_config": {
        Idioma.ES: "aviso: no se pudo leer la configuración global ({motivo})",
        Idioma.EN: "warning: the global configuration could not be read ({motivo})"},
}

_AGENTES = {"claude-code": Plataforma.CLAUDE_CODE, "opencode": Plataforma.OPENCODE}


def _version() -> str:
    """``X.Y.Z``: el núcleo numérico de la versión (sin ``.dev0`` ni etiquetas), en una sola línea estable."""
    try:
        completa = metadata.version("agentreach")
    except metadata.PackageNotFoundError:
        return "0.0.0"
    encontrada = re.match(r"\d+\.\d+\.\d+", completa)
    return encontrada.group(0) if encontrada else "0.0.0"


class _Parser(argparse.ArgumentParser):
    """Los errores de argumentos salen en el idioma elegido (variable o regional), sin traza."""

    def error(self, message: str):  # type: ignore[override]
        _decir(f"{_ERROR['argumentos'][resolver_idioma(None)]}: {escribir_peligrosos(message)[0]}")
        raise SystemExit(2)


_CON_VALOR = ("--tarea", "--directorio-de-trabajo", "--home", "--idioma", "--tono", "--tema", "--agente", "--color", "--salida", "--ancho")
_ARGUMENTOS: list[str] = []  # los argumentos de esta ejecución: ``--help`` los lee antes de que se procesen los demás


def _opcion_cruda(nombre: str) -> str | bool | None:
    """Valor de una opción mirando los argumentos sin procesar (``--help`` se ejecuta en mitad del análisis)."""
    for n, arg in enumerate(_ARGUMENTOS):
        if arg == nombre:
            if nombre in _CON_VALOR:
                return _ARGUMENTOS[n + 1] if n + 1 < len(_ARGUMENTOS) else None
            return True
        if arg.startswith(nombre + "="):
            return arg.split("=", 1)[1]
    return None


class _Ayuda(argparse.Action):
    """``--help``: el banner grande (solo en una terminal interactiva) y la ayuda."""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        lineas = _banner_segun_opciones(bool(_opcion_cruda("--no-banner")), bool(_opcion_cruda("--json")), False)
        if lineas:
            _escribir(sys.stdout, "\n".join(lineas) + "\n\n")
        _escribir(sys.stdout, parser.format_help())
        parser.exit()


def construir_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="agentreach",
        description=("Audita, en solo lectura, a qué puede acceder un agente de IA. Uso: agentreach audit RUTA (o agentreach RUTA); "
                     "agentreach doctor revisa la terminal."),
        add_help=False,
    )
    parser.add_argument("-h", "--help", action=_Ayuda, help="muestra esta ayuda")
    parser.add_argument("carpeta", nargs="?", help="carpeta del proyecto a auditar (solo lectura)")
    parser.add_argument("--version", action="version", version=f"agentreach {_version()}")
    # [SUPUESTO] nombres de los flags (Historias 5, 12, 13 y 13c). El opt-in está apagado por defecto.
    parser.add_argument(
        "--incluir-ubicaciones-sensibles",
        action="store_true",
        help="mira solo los metadatos de ~/.ssh, ~/.aws y ~/.npmrc (apagado por defecto)",
    )
    parser.add_argument("--tarea", metavar="TEXTO", help="lo que se le pedirá al agente: sirve para marcar lo ajeno a la tarea")
    parser.add_argument("--directorio-de-trabajo", metavar="RUTA", dest="trabajo",
                        help="carpeta donde se lanzará el agente (por defecto, la auditada): lo de fuera es ajeno")
    parser.add_argument("--home", metavar="RUTA", help="carpeta personal a mirar (por defecto, la del usuario)")
    parser.add_argument("--detalle", action="store_true", help="muestra códigos TH-n, motivos técnicos y fuente verificada")
    parser.add_argument("--idioma", choices=("es", "en", "auto"), default="auto", help="idioma del reporte (por defecto, automático)")
    parser.add_argument("--tono", choices=("cercano", "formal"), default=None,
                        help="tono del español: cercano (de tú, por defecto) o formal (de usted)")
    parser.add_argument("--tema", choices=("claro", "oscuro", "auto"), default=None,
                        help="colores para fondo claro u oscuro (por defecto, automático)")
    parser.add_argument("--agente", choices=tuple(_AGENTES), default=None, help="limita la auditoría a un agente")
    parser.add_argument("--color", choices=("auto", "siempre", "nunca"), default="auto", help="color del reporte")
    parser.add_argument("--ascii", action="store_true", help="solo símbolos ASCII y sin tildes en los símbolos")
    parser.add_argument("--no-banner", action="store_true", help="no muestra el banner de marca")
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)  # aún no existe: ya apaga el banner
    parser.add_argument("--salida", metavar="ARCHIVO", help="escribe el reporte en este archivo (UTF-8, sin color)")
    parser.add_argument("--formato", choices=("texto", "html"), default="texto",
                        help="formato del reporte: texto (por defecto) o html (un archivo estático; exige --salida)")
    parser.add_argument("--abrir", action="store_true", help="al terminar, abre el reporte HTML en el navegador (sin preguntar)")
    parser.add_argument("--no-abrir", action="store_true", dest="no_abrir", help="no abre el reporte en el navegador ni pregunta")
    parser.add_argument("--sin-reporte-html", action="store_true", dest="sin_reporte_html",
                        help="no crea el reporte HTML en AgentReach-reportes (carpeta personal)")
    parser.add_argument("--estricto", action="store_true", help="código de salida 1 también si hay entradas no revisadas")
    parser.add_argument("--ancho", type=int, metavar="N", help="ancho en columnas (solo para pruebas)")
    return parser


def _configuracion(args: argparse.Namespace, lectura_fuera: bool = True) -> Configuracion:
    """La configuración. Sin el permiso de segundo nivel NO se abre el archivo global (está en la carpeta personal)."""
    config = cargar_configuracion(
        flags={"incluir_ubicaciones_sensibles": args.incluir_ubicaciones_sensibles, "home": args.home},
        archivo_global=archivo_global_por_defecto() if lectura_fuera else None,
    )
    return dataclasses.replace(config, lectura_fuera=lectura_fuera)


def _comando(argv: list[str] | None) -> tuple[str, list[str]]:
    """``agentreach audit RUTA`` y ``agentreach RUTA`` son lo mismo; ``agentreach doctor`` es el otro comando.

    El comando es el primer argumento que no es una opción ni el valor de una opción: ``agentreach --tono formal doctor`` también vale.
    """
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    n = 0
    while n < len(argv):
        arg = argv[n]
        if arg in _CON_VALOR:
            n += 2
            continue
        if arg.startswith("-"):
            n += 1
            continue
        if arg in ("audit", "doctor"):
            return arg, argv[:n] + argv[n + 1:]
        break
    return "audit", argv


def parsear_argumentos(argv: list[str] | None = None) -> Configuracion:
    return _configuracion(construir_parser().parse_args(_comando(argv)[1]))


def idioma_regional() -> str | None:
    """Idioma de la configuración regional (dos letras) o ``None`` si no se puede leer."""
    try:
        if sys.platform == "win32":
            import ctypes

            buffer = ctypes.create_unicode_buffer(85)
            if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, 85):  # type: ignore[attr-defined]
                return buffer.value[:2].lower() or None
            return None
        for nombre in ("LC_ALL", "LC_MESSAGES", "LANG"):
            valor = os.environ.get(nombre, "")
            if valor:
                return valor[:2].lower()
    except (OSError, AttributeError, ValueError):
        return None
    return None


def idioma_con_origen(opcion: str | None) -> tuple[Idioma, str]:
    """El idioma y de dónde salió: ``--idioma`` gana a ``AGENTREACH_IDIOMA`` y esta a la regional; lo que no se entiende, español."""
    for candidato, origen in ((opcion, "opcion"), (os.environ.get("AGENTREACH_IDIOMA"), "variable")):
        texto = (candidato or "").lower()
        if texto in ("es", "en"):
            return Idioma(texto), origen
        if texto not in ("", "auto"):
            return Idioma.ES, "defecto"  # un valor que no se entiende cae en español, no en la regional
    regional = idioma_regional()
    if regional == "en":
        return Idioma.EN, "regional"
    return Idioma.ES, "regional" if regional == "es" else "defecto"


def resolver_idioma(opcion: str | None) -> Idioma:
    return idioma_con_origen(opcion)[0]


def resolver_tono(opcion: str | None) -> Tono:
    """``--tono`` gana a ``AGENTREACH_TONO``; por defecto, cercano."""
    for candidato in (opcion, os.environ.get("AGENTREACH_TONO")):
        texto = (candidato or "").lower()
        if texto in ("cercano", "formal"):
            return Tono(texto)
    return Tono.CERCANO


def _ancho(args: argparse.Namespace) -> int:
    if args.ancho:
        return max(args.ancho, 20)
    return ancho_de_trabajo(shutil.get_terminal_size(fallback=(80, 24)).columns)


def _columnas() -> int:
    """Columnas para los textos impresos (Historia 30): ``--ancho`` si se pidió, si no las de la terminal (80 sin terminal);
    entre 20 y 100. La ajustadora resta 1 (no se escribe en la última columna)."""
    pedido = _opcion_cruda("--ancho")
    try:
        columnas = int(pedido) if isinstance(pedido, str) else shutil.get_terminal_size(fallback=(80, 24)).columns
    except ValueError:
        columnas = 80
    return min(max(columnas, 20), 100)


_FINAL_PREGUNTA = re.compile(r" (\([SY]/N\)) $")


def _texto(texto: str) -> str:
    """UN solo punto por el que pasa todo texto impreso o pasado a una pregunta: ajusta cada línea al ancho de la terminal con
    ``formato.ajustar`` (sin partir palabras, respetando saltos de línea y la sangría de cada línea). El contenido no cambia.
    El «(S/N) » final no se separa de la palabra anterior ni pierde su espacio."""
    nbsp = "\ue000"  # marcador interno de uso privado: un U+00A0 real de una ruta o texto no se toca
    texto = _FINAL_PREGUNTA.sub(lambda m: nbsp + m.group(1) + " ", texto)
    ancho = _columnas()
    salida: list[str] = []
    for linea in texto.split("\n"):
        cuerpo = linea.strip(" ")
        if not cuerpo:
            salida.append(linea)
            continue
        sangria = len(linea) - len(linea.lstrip(" "))
        ajustadas = ajustar(cuerpo, ancho, sangria, sangria)
        if linea.endswith(" "):
            ajustadas[-1] += " "  # el espacio final de una pregunta (el cursor queda separado de «(S/N)»)
        salida.extend(ajustadas)
    return "\n".join(salida).replace(nbsp, " ")


def _decir(texto: str, flujo=None) -> None:
    """Imprime un mensaje ya ajustado (por defecto, en stderr)."""
    try:
        ajustado = _texto(texto)
    except Exception:  # noqa: BLE001 - los manejadores de último recurso nunca dejan traza: sin ajustar es mejor que nada
        ajustado = texto
    print(ajustado, file=flujo or sys.stderr)


def _es_terminal(flujo) -> bool:
    try:
        return bool(flujo.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def _es_utf8(flujo) -> bool:
    try:
        "■▲◊○√→·íó".encode(getattr(flujo, "encoding", None) or "utf-8")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _escribir(flujo, texto: str) -> None:
    codificacion = getattr(flujo, "encoding", None) or "utf-8"
    try:
        flujo.write(texto)
    except UnicodeEncodeError:  # una consola que no entiende un símbolo: se cambia por «?», nunca una traza
        flujo.write(texto.encode(codificacion, "replace").decode(codificacion))
    flujo.flush()


_SIN_DECIDIR = object()  # tema del banner sin resolver (``None`` ya significa «desconocido»)


def _banner_si_corresponde(
    tamano: Tamano, env, *, no_banner: bool, json: bool, salida: bool, color: Color | None = None, claro: bool | None | object = _SIN_DECIDIR,
    ascii_: bool | None = None,
) -> list[str]:
    """El banner si la salida es una terminal interactiva y nada lo apaga; si no, ninguna línea."""
    es_terminal = _es_terminal(sys.stdout)
    columnas = shutil.get_terminal_size(fallback=(80, 24)).columns if es_terminal else 0
    if not debe_mostrarse(es_terminal, env, no_banner, json, salida, columnas):
        return []
    unicode_ok = _es_utf8(sys.stdout)
    efectivo = tamano_efectivo(tamano, columnas, unicode_ok)
    if efectivo is None:
        return []
    if color is None:
        vt = activar_vt() if sys.platform == "win32" else True
        color = decidir_color("auto", True, env, sys.platform, vt)
    if claro is _SIN_DECIDIR:
        claro = resolver_tema_marca(None, env)
    usar_ascii = (not unicode_ok) if ascii_ is None else ascii_
    return banner(efectivo, _version(), ascii_=usar_ascii, color=color, claro=claro, ancho=columnas)


def _banner_segun_opciones(no_banner: bool, json: bool, salida: bool, tamano: Tamano = Tamano.GRANDE) -> list[str]:
    """El banner con el color, el tema y el ASCII que piden las opciones (leídas sin procesar)."""
    es_terminal = _es_terminal(sys.stdout)
    opcion_color = str(_opcion_cruda("--color") or "auto")
    vt = activar_vt() if es_terminal and sys.platform == "win32" and opcion_color != "nunca" else True
    color = decidir_color(opcion_color, es_terminal, os.environ, sys.platform, vt)
    claro = resolver_tema_marca(str(_opcion_cruda("--tema") or "") or None, os.environ)
    solo_ascii = bool(_opcion_cruda("--ascii")) or os.environ.get("AGENTREACH_ASCII") == "1" or not _es_utf8(sys.stdout)
    return _banner_si_corresponde(tamano, os.environ, no_banner=no_banner, json=json, salida=salida, color=color,
                                  claro=claro, ascii_=solo_ascii)


def main(argv: list[str] | None = None, ahora: Callable[[], datetime] | None = None,
         preguntar: Callable[[str], str] | None = None) -> int:
    comando, resto = _comando(argv)
    _ARGUMENTOS[:] = resto
    args = construir_parser().parse_args(resto)
    idioma = resolver_idioma(args.idioma)
    try:
        if comando == "doctor":
            return _doctor(args)
        return _ejecutar(args, idioma, ahora, preguntar or _preguntar_por_defecto)
    except KeyboardInterrupt:  # Ctrl+C: se corta sin traza, y lo que no se alcanzó a revisar no se muestra a medias
        _decir("\n" + _ERROR["cancelado_ctrl_c"][idioma])
        return 130
    except Exception:  # noqa: BLE001 - un error interno no deja traza ni un reporte a medias
        _decir(_ERROR["interno"][idioma])
        return 3


def _doctor(args: argparse.Namespace) -> int:
    idioma, origen = idioma_con_origen(args.idioma)
    tono = resolver_tono(args.tono)
    es_terminal = _es_terminal(sys.stdout)
    if not es_terminal:
        preparar_salida(sys.stdout)
    vt = activar_vt() if es_terminal and sys.platform == "win32" and args.color != "nunca" else True
    color = decidir_color(args.color, es_terminal, os.environ, sys.platform, vt)
    claro = resolver_tema(args.tema, os.environ)
    claro_marca = resolver_tema_marca(args.tema, os.environ)
    try:
        carpeta = args.carpeta or os.getcwd()
    except OSError:  # el directorio actual ya no existe: la comprobación de permisos lo dirá
        carpeta = os.path.join(os.sep, "carpeta-que-no-existe")
    if args.salida and _dentro(args.salida, carpeta):
        _decir(_ERROR["salida"][idioma])
        return 2
    if args.salida and os.path.lexists(args.salida):
        _decir(_ERROR["salida_existe"][idioma])
        return 2
    if args.salida:
        color = Color.NINGUNO
    entorno = Entorno(
        python=sys.version_info[:3], carpeta=carpeta, carpeta_indicada=bool(args.carpeta),
        codificacion=getattr(sys.stdout, "encoding", None) or "", es_terminal=es_terminal,
        columnas=shutil.get_terminal_size(fallback=(80, 24)).columns, env=os.environ, plataforma=sys.platform,
        color=color, color_activado=vt, idioma=idioma, origen_idioma=origen, color_opcion="nunca" if args.salida else args.color,
    )
    resultados = comprobar_entorno(entorno, tono)
    solo_ascii = args.ascii or os.environ.get("AGENTREACH_ASCII") == "1" or not _es_utf8(sys.stdout)
    lineas = _banner_si_corresponde(Tamano.MEDIANO, os.environ, no_banner=args.no_banner, json=args.json,
                                    salida=bool(args.salida), color=color, claro=claro_marca, ascii_=solo_ascii)
    if lineas:
        lineas = [*_ESPACIO_ANTES, *lineas, *_ESPACIO_DESPUES]  # aire alrededor del banner: tres líneas en blanco antes y después
    texto = formatear_doctor(resultados, idioma, _version(), ancho=_ancho(args), ascii_=solo_ascii, color=color, claro=claro,
                             banner=lineas or None, simbolos_ascii=solo_ascii or not es_terminal)
    if args.salida:
        try:
            with open(args.salida, "x", encoding="utf-8", newline="\n") as f:
                f.write(texto)
        except FileExistsError:
            _decir(_ERROR["salida_existe"][idioma])
            return 2
        except OSError:
            _decir(_ERROR["escritura"][idioma])
            return 2
        return codigo_doctor(resultados)
    try:
        _escribir(sys.stdout, texto)
    except OSError as error:
        if not isinstance(error, BrokenPipeError) and error.errno not in (errno.EPIPE, errno.EINVAL):
            raise
    return codigo_doctor(resultados)


INTENTOS = 3  # veces que se repite una pregunta antes de rendirse
_resumen_corto_por_defecto = True  # solo las pruebas lo cambian (para comparar el listado completo sin repetir --detalle)
_crear_reporte_por_defecto = True  # solo las pruebas lo cambian (sin escribir en la carpeta personal)
_preguntar_por_defecto = input  # solo las pruebas lo cambian: la línea de comandos no tiene ninguna opción que responda por la persona


def _confirmar(preguntar: Callable[[str], str], texto: str, idioma: Idioma) -> bool | None:
    """``True`` con s o S (en inglés, y o Y), ``False`` con n o N. Cualquier otra cosa (Enter solo, «si», «yes», espacios...) NO decide: se vuelve a
    preguntar, y tras ``INTENTOS`` intentos (o con la entrada cerrada) devuelve ``None``: no hubo respuesta y no se hace nada."""
    for _ in range(INTENTOS):
        try:
            respuesta = preguntar(_texto(texto))
        except EOFError:
            return None
        if respuesta in (("y", "Y") if idioma is Idioma.EN else ("s", "S")):
            return True
        if respuesta in ("n", "N"):
            return False
        _decir(_ERROR["solo_sn"][idioma])
    return None


def _interactivo() -> bool:
    """Una persona delante: la entrada y la salida son una terminal. Sin ella AgentReach no lee nada (no hay un permiso que lo salte)."""
    return _es_terminal(sys.stdin) and _es_terminal(sys.stdout)


def _carpeta_actual(idioma: Idioma) -> str | None:
    try:
        return os.getcwd()
    except OSError:
        _decir(_ERROR["carpeta"][idioma])
        return None


def _tipo_riesgoso(carpeta: str, home: str) -> str | None:
    """La carpeta personal y la raíz de un disco se piden con más cuidado: recorrerlas toca ubicaciones sensibles."""
    real = os.path.normcase(os.path.realpath(carpeta))
    if os.path.dirname(real) == real:
        return "tipo_raiz"
    if home:
        real_home = os.path.normcase(os.path.realpath(home))
        if real_home == real:
            return "tipo_home"
        try:
            if os.path.commonpath([real_home, real]) == real:
                return "tipo_contiene_home"  # p. ej. C:\\Users: recorrerla toca la carpeta personal de varias personas
        except ValueError:  # otra unidad de disco
            pass
    return None


def _presentar(lineas: list[str], idioma: Idioma) -> None:
    """El banner (con su aire) y qué es AgentReach, qué hace y qué no, antes de pedir permiso."""
    if lineas:
        _escribir(sys.stdout, "\n".join(lineas) + "\n\n")
    _decir("\n".join(_ERROR[k][idioma] for k in ("intro_que", "intro_hace", "intro_no_hace")) + "\n")


def _pedir_lectura(carpeta: str, args: argparse.Namespace, idioma: Idioma, preguntar: Callable[[str], str]) -> bool:
    """Pide permiso para leer la carpeta (solo s, S, n y N cuentan). Sin una respuesta válida, o con n, no se lee nada."""
    escrita = os.path.abspath(carpeta)
    visible = escribir_peligrosos(escrita)[0]
    real = os.path.realpath(escrita)
    if os.path.normcase(real) != os.path.normcase(escrita):  # un enlace, o nombres cortos de Windows: se muestra también la ruta real
        visible += chr(10) + "  " + _ERROR["ruta_real"][idioma].format(real=escribir_peligrosos(real)[0])
    tipo = _tipo_riesgoso(carpeta, args.home or os.path.expanduser("~"))
    aviso = _ERROR["aviso_riesgosa"][idioma].format(tipo=_ERROR[tipo][idioma]) if tipo else ""
    respuesta = _confirmar(preguntar, _ERROR["pregunta_leer"][idioma].format(ruta=visible, aviso=aviso), idioma)
    if respuesta:
        return True
    clave = "no_leyo" if respuesta is False else "sin_respuesta_carpeta"
    _decir(_ERROR[clave][idioma].format(n=INTENTOS))
    return False


def _pedir_reglas(args: argparse.Namespace, idioma: Idioma, tono: Tono, preguntar: Callable[[str], str]) -> bool:
    """Segundo nivel: ¿se permite ver las reglas de los agentes en la carpeta personal (y la configuración gestionada y el opencode.json
    de las carpetas padre)? Solo con S (o Y en inglés). Con N, o sin una respuesta válida, no se lee NADA fuera del proyecto."""
    respuesta = _confirmar(preguntar, _PREGUNTA_REGLAS[(idioma, tono)], idioma)
    if respuesta:
        return True
    clave = "sin_reglas" if respuesta is False else "sin_respuesta_reglas"
    _decir(_ERROR[clave][idioma].format(n=INTENTOS))
    return False


def _reporte_html(datos, carpeta: str, args: argparse.Namespace, idioma: Idioma, tono: Tono, momento: datetime,
                  preguntar: Callable[[str], str]) -> None:
    """Crea el reporte HTML en ``AgentReach-reportes`` (carpeta personal, fuera de la revisada), dice dónde quedó y, si la persona
    quiere (``--abrir``, su respuesta recordada o la que da ahora), lo abre en el navegador. Nada de esto cambia el código de salida."""
    home = args.home or os.path.expanduser("~")
    flujo = sys.stdout
    try:
        html = generar_html(datos, idioma=idioma, tono=tono, version=_version(), agente=_AGENTES.get(args.agente or ""))
        resultado = escribir_reporte(html, home, carpeta, momento)
    except ReporteDemasiadoGrande:
        _decir(_ERROR["reporte_no"][idioma].format(motivo=_ERROR["motivo_demasiado_grande"][idioma]))
        return
    if resultado.ruta is None:
        _decir(_ERROR["reporte_no"][idioma].format(motivo=_ERROR["motivo_" + resultado.motivo][idioma]))
        return
    _escribir(flujo, _texto("\n" + _ERROR["reporte_donde"][idioma].format(ruta=escribir_peligrosos(resultado.ruta)[0]) + "\n"
                            + _ERROR["reporte_que"][idioma]) + "\n")
    abrir = False
    if args.abrir:
        abrir = True
    elif not args.no_abrir:
        recordada = leer_preferencia(home, carpeta)
        if recordada is None:
            respuesta = _confirmar(preguntar, _ERROR["pregunta_abrir"][idioma], idioma)
            abrir = bool(respuesta)
            if respuesta is None:  # sin una respuesta válida no se decide nada: ni se abre ni se recuerda
                _decir(_ERROR["sin_respuesta_abrir"][idioma].format(n=INTENTOS))
            else:
                guardada = guardar_preferencia(home, carpeta, abrir)
                if guardada:
                    _escribir(flujo, _texto(_ERROR["respuesta_guardada"][idioma].format(ruta=escribir_peligrosos(guardada)[0])) + "\n")
        else:
            abrir = recordada
    if abrir and not abrir_navegador(resultado.ruta):
        _decir(_ERROR["no_abrio"][idioma])


def _ejecutar(args: argparse.Namespace, idioma: Idioma, ahora: Callable[[], datetime] | None,
              preguntar: Callable[[str], str]) -> int:
    carpeta = args.carpeta
    tono = resolver_tono(args.tono)
    if args.json:
        _decir(_ERROR["json"][idioma])
        return 2
    if not _interactivo():  # sin una persona delante no se lee nada (ni se mira si la carpeta existe), y no hay permiso que lo salte
        _decir(_ERROR["sin_terminal"][idioma])
        return 2
    if carpeta is None:  # sin ruta se revisa la carpeta actual
        carpeta = _carpeta_actual(idioma)
        if carpeta is None:
            return 2
    if not os.path.isdir(carpeta):
        _decir(_ERROR["carpeta"][idioma])
        return 2
    if args.formato == "html" and not args.salida:
        _decir(_ERROR["html_sin_salida"][idioma])
        return 2
    if args.salida and _dentro(args.salida, carpeta):
        _decir(_ERROR["salida"][idioma])
        return 2
    if args.salida and os.path.lexists(args.salida):  # antes de pedir permiso ni leer nada: no se pisa un archivo que ya existe
        _decir(_ERROR["salida_existe"][idioma])
        return 2
    es_terminal = not args.salida and _es_terminal(sys.stdout)
    if not es_terminal and not args.salida:
        preparar_salida(sys.stdout)  # una redirección o tubería: UTF-8 sin trazas
        preparar_salida(sys.stderr)
    solo_ascii = args.ascii or os.environ.get("AGENTREACH_ASCII") == "1" or (es_terminal and not _es_utf8(sys.stdout))
    vt = activar_vt() if es_terminal and sys.platform == "win32" and args.color != "nunca" else True
    color = decidir_color("nunca" if args.salida else args.color, es_terminal, os.environ, sys.platform, vt)
    claro = resolver_tema(args.tema, os.environ)
    claro_marca = resolver_tema_marca(args.tema, os.environ)
    lineas = _banner_si_corresponde(Tamano.MEDIANO, os.environ, no_banner=args.no_banner, json=args.json, salida=bool(args.salida),
                                    color=color, claro=claro_marca, ascii_=solo_ascii or not es_terminal)
    if lineas:
        lineas = [*_ESPACIO_ANTES, *lineas, *_ESPACIO_DESPUES]  # aire alrededor del banner: tres líneas en blanco antes y después
    _presentar(lineas, idioma)
    if not _pedir_lectura(carpeta, args, idioma, preguntar):
        return 2
    lectura_fuera = _pedir_reglas(args, idioma, tono, preguntar)  # segundo nivel: las reglas de los agentes fuera del proyecto
    config = _configuracion(args, lectura_fuera)
    for n in config.no_revisados:  # el opt-in queda apagado: se avisa en vez de callarlo
        motivo = TITULO_MOTIVO[n.motivo][idioma] + (f" [{n.motivo.value}]" if args.detalle else "")
        _decir(_ERROR["aviso_config"][idioma].format(motivo=motivo))
    resultado = auditar(carpeta, config, tarea=args.tarea, trabajo=args.trabajo)
    momento = (ahora or datetime.now)()
    datos = preparar(
        resultado, carpeta, ahora=momento, estricto=args.estricto,
        home=args.home or os.path.expanduser("~"), agente=_AGENTES.get(args.agente or ""),
    )
    if args.formato == "html":  # un solo archivo; si algo falla (topes, plantilla) no se escribe nada: código 3, sin reporte parcial
        texto = generar_html(datos, idioma=idioma, tono=tono, version=_version(), agente=_AGENTES.get(args.agente or ""))
    else:
        texto = generar(
            datos, idioma, detalle=args.detalle, ancho=_ancho(args), ascii_=solo_ascii, color=color,
            fondo_claro=claro, simbolos_ascii=solo_ascii or not es_terminal, tono=tono,
            corto=_resumen_corto_por_defecto and not args.detalle and not args.salida,  # la terminal muestra el resumen; el archivo y --detalle, el listado completo
        )
    if args.salida:
        try:
            with open(args.salida, "x", encoding="utf-8", newline="\n") as f:  # "x": falla si ya existe (nada se pisa)
                f.write(texto)
        except FileExistsError:
            _decir(_ERROR["salida_existe"][idioma])
            return 2
        except OSError:
            _decir(_ERROR["escritura"][idioma])
            return 2
    else:
        try:
            _escribir(sys.stdout, texto)
        except OSError as error:  # BrokenPipeError incluido
            if not isinstance(error, BrokenPipeError) and error.errno not in (errno.EPIPE, errno.EINVAL):
                raise  # un disco lleno o un error de E/S no es «quien lee cerró la tubería»: sale como error interno
            # quien lee cerró la tubería: el código de salida sigue siendo el calculado
            try:
                destino = os.open(os.devnull, os.O_WRONLY)
                try:
                    os.dup2(destino, sys.stdout.fileno())  # que el cierre del intérprete no vuelva a fallar
                finally:
                    os.close(destino)
            except (OSError, ValueError, AttributeError):
                pass
    if args.formato == "texto" and not args.salida and not args.sin_reporte_html and _crear_reporte_por_defecto:
        _reporte_html(datos, carpeta, args, idioma, tono, momento, preguntar)
    return datos.codigo_de_salida
