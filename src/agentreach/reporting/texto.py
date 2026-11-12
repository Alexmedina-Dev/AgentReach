"""Reporte de terminal (Historia 13, contenido): arma el texto completo desde las vistas de la compuerta.

Solo conoce ``DatosReporte`` y los catálogos fijos: no ve un ``Finding`` ni el texto de ningún archivo. El ancho, el color y
la codificación son de la Historia 13b (``reporting/formato.py``): el texto sale ajustado a ``ancho`` columnas, sin cortar
palabras ni rutas, y el color se aplica después de ajustar.

Estructura, siempre en este orden: encabezado, aviso de secretos, resumen, reglas de los agentes (contexto), hallazgos por
nivel y por archivo, «No se pudo revisar» (A: esta carpeta; B: límites fijos de FR-21) y cierre con el código de salida.
Los códigos ``TH-n`` y los identificadores de motivo salen solo con ``detalle``.
"""

from __future__ import annotations

import unicodedata
from collections import Counter

from agentreach.contracts import (
    Idioma,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    Plataforma,
    texto_de_motivo,
)
from agentreach.core.autocomprobacion import RazonCorreccion
from agentreach.core.catalogo_explicaciones import (
    AJENO,
    LIMITES,
    LIMITES_TAMBIEN,
    NIVEL,
    POSTURA,
    PROVEEDOR,
    TITULO_MOTIVO,
    Tono,
    como_resolver,
    que_hacer,
    que_significa,
    titulo_corto,
)
from agentreach.core.catalogo_terminos import Termino, etiquetas, explicacion, punto_ciego
from agentreach.core.catalogo_terminos import linea as linea_de
from agentreach.core.catalogo_terminos import nombre as nombre_de
from agentreach.reporting.formato import Color, ajustar, ancho_visible, pintar, ultima_comprobacion
from agentreach.reporting.gate import CorreccionVista, DatosReporte, HallazgoVista
from agentreach.reporting.limpieza import escribir_peligrosos

__all__ = ["generar"]

_AMBITOS = {Idioma.ES: {"proyecto": "proyecto", "usuario": "usuario", "entorno": "entorno"},
            Idioma.EN: {"proyecto": "project", "usuario": "user", "entorno": "environment"}}
_SIMBOLO = {Nivel.COMPROBADO: "■", Nivel.POTENCIAL: "▲", Nivel.HIPOTESIS: "◊"}
_NBSP = chr(0xA0)
_ROL_NIVEL = {Nivel.COMPROBADO: "comprobado", Nivel.POTENCIAL: "potencial", Nivel.HIPOTESIS: "hipotesis"}
_SIMBOLO_ASCII = {Nivel.COMPROBADO: "[!!]", Nivel.POTENCIAL: "[!]", Nivel.HIPOTESIS: "[?]"}

_TERMINO_NIVEL = {Nivel.COMPROBADO: Termino.NIVEL_COMPROBADO, Nivel.POTENCIAL: Termino.NIVEL_POTENCIAL, Nivel.HIPOTESIS: Termino.NIVEL_HIPOTESIS}


def _es_hook(causa) -> bool:
    return causa.clave.lower().startswith("hook")


def _es_sandbox(causa) -> bool:
    return causa.clave.lower().startswith("sandbox")


_T: dict[str, dict[Idioma, str]] = {
    "titulo": {Idioma.ES: "Reporte de revisión", Idioma.EN: "Review report"},
    "carpeta": {Idioma.ES: "Carpeta revisada", Idioma.EN: "Folder reviewed"},
    "fecha": {Idioma.ES: "Fecha", Idioma.EN: "Date"},
    "solo_lectura": {
        Idioma.ES: "Solo lectura: AgentReach no cambió nada del proyecto ni ejecutó sus programas.",
        Idioma.EN: "Read-only: AgentReach changed nothing in the project and ran none of its programs."},
    "aviso": {
        Idioma.ES: ("(i) No se muestran valores de secretos. AgentReach nunca copia contraseñas, tokens ni claves: "
                    "solo dice dónde están y de qué tipo son."),
        Idioma.EN: ("(i) No secret values are shown. AgentReach never copies passwords, tokens or keys: "
                    "it only says where they are and what type they are.")},
    "resumen": {Idioma.ES: "RESUMEN", Idioma.EN: "SUMMARY"},
    "archivos": {Idioma.ES: "archivos mirados", Idioma.EN: "files looked at"},
    "no_revisar": {Idioma.ES: "NO SE PUDO REVISAR", Idioma.EN: "COULD NOT CHECK"},
    "desc_no_revisar": {
        Idioma.ES: "huecos de cobertura, no un veredicto", Idioma.EN: "coverage gaps, not a verdict"},
    "intro_comprobado": {
        Idioma.ES: "Exposición confirmada. Se atiende primero.", Idioma.EN: "Exposure confirmed. Handle first."},
    "intro_potencial": {
        Idioma.ES: "Probable, pero falta confirmar algo. Revisar pronto: potencial no quiere decir riesgo menor. El motivo está en cada hallazgo.",
        Idioma.EN: "Likely, but something is left to confirm. Review soon: potential does not mean lower risk. The reason is in each finding."},
    "intro_hipotesis": {
        Idioma.ES: "Sugerencias, no accesos comprobados.", Idioma.EN: "Suggestions, not verified access."},
    "sin_hallazgos": {Idioma.ES: "SIN HALLAZGOS", Idioma.EN: "NO FINDINGS"},
    "sin_hallazgos_frase": {
        Idioma.ES: "Eso no significa que el agente no pueda hacer daño: lee qué no se pudo revisar.",
        Idioma.EN: "That does not mean the agent cannot do harm: read what could not be checked."},
    "linea": {Idioma.ES: "línea", Idioma.EN: "line"},
    "linea_nd": {Idioma.ES: "línea no determinada", Idioma.EN: "line not determined"},
    "nivel_y_por_que": {Idioma.ES: "Nivel y por qué", Idioma.EN: "Level and why"},
    "plataforma": {Idioma.ES: "Plataforma y agente", Idioma.EN: "Platform and agent"},
    "reglas": {Idioma.ES: "Reglas del agente", Idioma.EN: "Agent rules"},
    "ajeno": {Idioma.ES: "Ajeno a la tarea", Idioma.EN: "Unrelated to the task"},
    "que_hacer": {Idioma.ES: "Qué hacer", Idioma.EN: "What to do"},
    "que_significa": {Idioma.ES: "Qué significa", Idioma.EN: "What it means"},
    "igual": {
        Idioma.ES: "Qué hacer / qué significa: igual que el hallazgo de la línea {n} de este archivo",
        Idioma.EN: "What to do / what it means: same as the finding on line {n} of this file"},
    "regla_en": {Idioma.ES: "regla en", Idioma.EN: "rule in"},
    "no_determinada": {Idioma.ES: "no determinada", Idioma.EN: "not determined"},
    "reglas_titulo": {Idioma.ES: "REGLAS DE LOS AGENTES (contexto)", Idioma.EN: "AGENT RULES (context)"},
    "reglas_intro": {
        Idioma.ES: "Son las reglas que cada agente declara. Rodean a los hallazgos; no son hallazgos por sí solas.",
        Idioma.EN: "These are the rules each agent declares. They surround the findings; they are not findings by themselves."},
    "limpieza": {
        Idioma.ES: "quita las credenciales del entorno de los programas que lanza (medida de protección)",
        Idioma.EN: "removes credentials from the environment of the programs it launches (protection measure)"},
    "sin_reglas": {Idioma.ES: "sin reglas de permisos en la configuración", Idioma.EN: "no permission rules in the configuration"},
    "no_revisar_titulo": {Idioma.ES: "QUÉ NO PUDO REVISAR AGENTREACH", Idioma.EN: "WHAT AGENTREACH COULD NOT CHECK"},
    "parte_a": {Idioma.ES: "A. En esta carpeta", Idioma.EN: "A. In this folder"},
    "parte_a_intro": {
        Idioma.ES: "Las rutas que empiezan con ~ están en tu carpeta personal.",
        Idioma.EN: "Paths that start with ~ are in your home folder."},
    "nada": {Idioma.ES: "(nada en esta carpeta)", Idioma.EN: "(nothing in this folder)"},
    "como_resolver": {Idioma.ES: "Cómo resolverlo", Idioma.EN: "How to fix it"},
    "parte_b": {Idioma.ES: "B. Límites de la herramienta", Idioma.EN: "B. Limits of the tool"},
    "parte_b_intro": {
        Idioma.ES: "Esto AgentReach no lo puede ver. Ver una condición en un archivo no es ver el ataque.",
        Idioma.EN: "AgentReach cannot see this. Seeing a condition in a file is not seeing the attack."},
    "escritos": {
        Idioma.ES: "Algunos nombres traían caracteres invisibles o de control; se muestran escritos como \\uXXXX.",
        Idioma.EN: "Some names had invisible or control characters; they are shown written as \\uXXXX."},
    "corr_bajo": {
        Idioma.ES: "Se bajó de {antes} a {despues}: {tipo}, {ruta}.", Idioma.EN: "Lowered from {antes} to {despues}: {tipo}, {ruta}."},
    "corr_bajo_a": {Idioma.ES: "Se bajó a {despues}: {tipo}, {ruta}.", Idioma.EN: "Lowered to {despues}: {tipo}, {ruta}."},
    "corr_sin_linea": {
        Idioma.ES: "Sigue en {despues}, sin línea: {tipo}, {ruta}.", Idioma.EN: "Stays at {despues}, line removed: {tipo}, {ruta}."},
    "corr_corregido": {Idioma.ES: "Se corrigió: {tipo}, {ruta}.", Idioma.EN: "Corrected: {tipo}, {ruta}."},
    "corr_mas": {Idioma.ES: "y {n} más.", Idioma.EN: "and {n} more."},
    "corr_generico": {
        Idioma.ES: "Se corrigieron {n} hallazgo(s) antes de imprimir.", Idioma.EN: "{n} finding(s) were corrected before printing."},
    "terminos_titulo": {Idioma.ES: "CÓMO LEER ESTE REPORTE", Idioma.EN: "HOW TO READ THIS REPORT"},
    "nd_hook": {
        Idioma.ES: "AgentReach no sabe qué decide ese programa", Idioma.EN: "AgentReach does not know what that program decides"},
    "nd_sandbox": {
        Idioma.ES: "AgentReach no sabe interpretar esa caja de aislamiento", Idioma.EN: "AgentReach cannot interpret that isolation box"},
    "cierre": {Idioma.ES: "Código de salida", Idioma.EN: "Exit code"},
    "salida_0": {Idioma.ES: "no hay hallazgos comprobados", Idioma.EN: "no verified findings"},
    "salida_1": {Idioma.ES: "hay hallazgos comprobados", Idioma.EN: "there are verified findings"},
    "salida_1_estricto": {
        Idioma.ES: "--estricto: hay entradas que no se pudieron revisar", Idioma.EN: "--estricto: some entries could not be checked"},
    "cfg_titulo": {Idioma.ES: "AGENTES CONFIGURADOS", Idioma.EN: "CONFIGURED AGENTS"},
    "cfg_intro": {
        Idioma.ES: "Según los archivos de configuración que existen. No significa que el agente se haya ejecutado.",
        Idioma.EN: "According to the configuration files that exist. It does not mean the agent has run."},
    "cfg_high": {Idioma.ES: "configurado", Idioma.EN: "configured"},
    "cfg_potential": {Idioma.ES: "probablemente configurado", Idioma.EN: "probably configured"},
    "cfg_hypothesis": {Idioma.ES: "solo un indicio", Idioma.EN: "hint only"},
    "cfg_marco": {Idioma.ES: "marco instalado sobre {sobre}", Idioma.EN: "framework installed on {sobre}"},
    "cfg_un_agente": {Idioma.ES: "un agente", Idioma.EN: "an agent"},
    "cfg_no_analiza": {Idioma.ES: "AgentReach aún no analiza qué puede alcanzar", Idioma.EN: "AgentReach does not analyze what it can reach yet"},
    "cfg_indeterminado": {
        Idioma.ES: "No determinado: {ruta} lo leen varios agentes ({candidatos}); no dice cuál está configurado.",
        Idioma.EN: "Not determined: {ruta} is read by several agents ({candidatos}); it does not say which one is configured."},
    "nd_titulo": {Idioma.ES: "POR QUÉ HAY NIVELES «NO DETERMINADO»", Idioma.EN: "WHY SOME LEVELS ARE \"NOT DETERMINED\""},
    "nd_afecta": {Idioma.ES: "{n} hallazgos dependen de esto", Idioma.EN: "{n} findings depend on this"},
    "urgentes": {Idioma.ES: "LO MÁS URGENTE", Idioma.EN: "MOST URGENT"},
    "urgentes_de": {Idioma.ES: "{n} de {total}", Idioma.EN: "{n} of {total}"},
    "alcance_corto": {
        Idioma.ES: ("Esto cubre solo lo que AgentReach pudo revisar. No significa que lo demás sea seguro: "
                    "lo que no se pudo revisar y los límites están en el reporte visual y en --detalle."),
        Idioma.EN: ("This covers only what AgentReach could check. It does not mean the rest is safe: "
                    "what could not be checked and the limits are in the visual report and in --detalle.")},
    "pista_corta": {
        Idioma.ES: "Para ver el listado completo, con códigos y motivos técnicos, ejecuta con --detalle.",
        Idioma.EN: "To see the full list, with codes and technical reasons, run with --detalle."},
    "pista": {
        Idioma.ES: "Para ver los códigos y los motivos técnicos, ejecuta con --detalle.",
        Idioma.EN: "To see the codes and technical reasons, run with --detalle."},
    "codigo_catalogo": {Idioma.ES: "Código del catálogo", Idioma.EN: "Catalog code"},
    "ubicacion": {Idioma.ES: "Ubicación", Idioma.EN: "Location"},
    "motivo_tecnico": {Idioma.ES: "Motivo técnico", Idioma.EN: "Technical reason"},
    "fuente": {Idioma.ES: "Fuente verificada", Idioma.EN: "Verified source"},
    "si": {Idioma.ES: "sí", Idioma.EN: "yes"},
    "no": {Idioma.ES: "no", Idioma.EN: "no"},
}
_T["seccion_agente"] = {Idioma.ES: "AGENTE", Idioma.EN: "AGENT"}
_T["seccion_general"] = {
    Idioma.ES: "SIN AGENTE ESPECÍFICO", Idioma.EN: "NOT TIED TO A SPECIFIC AGENT"}
# Lo que cambia en español formal (de usted); lo demás no usa pronombres y se comparte.
_T_FORMAL = {
    "sin_hallazgos_frase": "Eso no significa que el agente no pueda hacer daño: lea qué no se pudo revisar.",
    "parte_a_intro": "Las rutas que empiezan con ~ están en su carpeta personal.",
    "pista": "Para ver los códigos y los motivos técnicos, ejecute con --detalle.",
    "pista_corta": "Para ver el listado completo, con códigos y motivos técnicos, ejecute con --detalle.",
}
_T["esquema_1.x"] = {
    Idioma.ES: "Configuración (versión 1.x) detectada por la forma de los archivos (no prueba la versión instalada).",
    Idioma.EN: "Configuration (version 1.x) detected from the shape of the files (it does not prove the installed version)."}
_T["esquema_2.x"] = {
    Idioma.ES: "Configuración (versión 2.x) detectada por la forma de los archivos (no prueba la versión instalada).",
    Idioma.EN: "Configuration (version 2.x) detected from the shape of the files (it does not prove the installed version)."}
_T["esquema_ambiguo"] = {
    Idioma.ES: "No se pudo determinar la versión de opencode; se asume el peor caso (2.x): por ejemplo, leer fuera del proyecto se permite sin preguntar.",
    Idioma.EN: "The opencode version could not be determined; the worst case (2.x) is assumed: for example, reading outside the project is allowed without asking."}
_PLATAFORMA = {
    Plataforma.CLAUDE_CODE: "Claude Code",
    Plataforma.OPENCODE: "opencode",
}


def _t(clave: str, idioma: Idioma) -> str:
    return _T[clave][idioma]


def _ascii(texto: str) -> str:
    """Todo a ASCII: sin tildes, ``·`` como ``-`` y lo que no tenga forma como ``?``."""
    sin_marcas = "".join(c for c in unicodedata.normalize("NFKD", texto.replace("·", "-").replace("«", '"').replace("»", '"')) if not unicodedata.combining(c))
    return "".join(c if ord(c) < 128 else "?" for c in sin_marcas)


class _Texto:
    def __init__(
        self, d: DatosReporte, idioma: Idioma, detalle: bool, ancho: int, simbolos_ascii: bool, forzar_nota: bool = False,
        tono: Tono = Tono.CERCANO, corto: bool = False,
    ) -> None:
        self.corto = corto  # el resumen de la terminal: por nivel y lo más urgente, sin volcar todo el listado
        self.d, self.i, self.detalle, self.ancho, self.ascii = d, idioma, detalle, ancho, simbolos_ascii
        self.tono = tono
        dinamicos = [d.carpeta, *(h.ruta for h in d.hallazgos), *(n.ruta for n in d.no_revisados),
                     *(r.herramienta for r in d.reglas), *(r.ubicacion for r in d.reglas),
                     *(h.regla for h in d.hallazgos if h.regla), *(h.agente for h in d.hallazgos if h.agente),
                     *(c.ruta for c in d.correcciones)]
        # fichas indivisibles: una ruta con espacios dentro de una frase se trata como una sola palabra
        self.protegidas = sorted({t for t in dinamicos if " " in t}, key=len, reverse=True)
        # segunda barrera: lo dinámico se vuelve a escribir al imprimir; si algo cambia, la nota sale (se decide al final)
        self.cambio = False
        self.nota_de_nombres = d.hubo_nombres_escritos or forzar_nota
        self.salida: list[tuple[str, str | None]] = []  # (línea de texto plano, rol de color)
        self.dichos: set[Termino] = set()  # cada término se explica una sola vez por reporte

    def _t(self, clave: str, idioma: Idioma | None = None) -> str:
        if self.i is Idioma.ES and self.tono is Tono.FORMAL and clave in _T_FORMAL:
            return _T_FORMAL[clave]
        return _T[clave][self.i]

    def linea(self, texto: str = "", primera: int = 0, resto: int | None = None, rol: str | None = None) -> None:
        if not texto:
            self.salida.append(("", None))
            return
        seguro = self._seguro(texto)
        for ficha in self.protegidas:
            seguro = seguro.replace(ficha, ficha.replace(" ", _NBSP))
        for parte in ajustar(seguro, self.ancho, primera, resto):
            self.salida.append((parte.replace(_NBSP, " "), rol))

    def _seguro(self, texto: str) -> str:
        escrito, cambio = escribir_peligrosos(texto, recortar=False)
        self.cambio = self.cambio or cambio
        return escrito

    def crudo(self, texto: str, rol: str | None = None) -> None:
        self.salida.append((self._seguro(texto), rol))

    def termino(self, termino: Termino, sangria: int = 2, rol: str | None = "info") -> None:
        """La frase de terminal del término (Historia 32): solo la primera vez y solo donde el término aparece."""
        if termino in self.dichos:
            return
        self.dichos.add(termino)
        self.linea(linea_de(termino, self.i, self.tono), sangria, sangria, rol=rol)

    def etiquetada(self, etiqueta: str, ruta: str, sangria: int = 0) -> None:
        """``etiqueta ruta`` en una línea si cabe; si no, la ruta entera en su propia línea."""
        if sangria + ancho_visible(etiqueta) + 1 + ancho_visible(ruta) < self.ancho:
            self.crudo(" " * sangria + f"{etiqueta} {ruta}")
        else:
            self.ruta(ruta, sangria, etiqueta)

    def ruta(self, ruta: str, sangria: int = 0, antes: str = "", rol: str | None = None) -> None:
        """Una ruta nunca se parte: va entera en su línea (la terminal la parte sola si es más larga que el ancho)."""
        if antes:
            self.linea(antes, sangria, rol=rol)
            self.crudo(" " * (sangria + 2) + ruta, rol)
        else:
            self.crudo(" " * sangria + ruta, rol)

    def simbolo(self, nivel: Nivel) -> str:
        return (_SIMBOLO_ASCII if self.ascii else _SIMBOLO)[nivel]

    # ---- partes --------------------------------------------------------------------------------------------

    def encabezado(self) -> None:
        i = self.i
        titulo = f"AGENTREACH  {self._t('titulo', i)}"
        self.crudo(titulo)
        self.crudo("=" * len(titulo))
        self.etiquetada(f"{self._t('carpeta', i)}:", self.d.carpeta)
        self.linea(f"{self._t('fecha', i)}: {self.d.fecha.strftime('%Y-%m-%d %H:%M')}")
        self.linea(self._t("solo_lectura", i), rol="info")
        self.linea()
        self.linea(self._t("aviso", i), 0, 4, rol="info")
        self.linea()

    def resumen(self) -> None:
        i, d = self.i, self.d
        self.linea(f"{self._t('resumen', i)}  ({d.archivos_mirados} {self._t('archivos', i)})")
        for plataforma, grupo in self._secciones():  # los niveles nunca se mezclan entre agentes
            self.linea(self._titulo_seccion(plataforma), 2)
            cuenta = Counter(h.nivel for h in grupo)
            for nivel in (Nivel.COMPROBADO, Nivel.POTENCIAL, Nivel.HIPOTESIS):
                if cuenta[nivel]:
                    self.linea(f"{self.simbolo(nivel)} {NIVEL[nivel][i]}  {cuenta[nivel]}", 4, 6, rol=_ROL_NIVEL[nivel])
        self.linea(f"{'[-]' if self.ascii else '○'} {self._t('no_revisar', i)}  {len(d.no_revisados)}  {self._t('desc_no_revisar', i)}",
                   2, 4, rol="no_revisar")  # la explicación larga de «no se pudo revisar» sale con --detalle
        for nivel, term in _TERMINO_NIVEL.items():  # la frase de cada nivel presente, una vez
            if any(h.nivel is nivel for h in d.hallazgos):
                self.termino(term, 2, rol=_ROL_NIVEL[nivel])
        self.linea()
        self.autocomprobacion()
        if self.nota_de_nombres:
            self.linea(self._t("escritos", i), rol="info")
            self.linea()

    def _aviso_correccion(self, c: CorreccionVista) -> str:
        """Cuál hallazgo cambió y a qué nivel pasó: tipo y ruta, nunca valores."""
        i = self.i
        tipo = titulo_corto(c.tipo, i)
        datos = {"tipo": tipo[:1].lower() + tipo[1:], "ruta": c.ruta}
        if c.nivel_despues is None:
            return self._t("corr_corregido").format(**datos)
        datos["despues"] = NIVEL[c.nivel_despues][i].lower()
        if c.nivel_antes is None:
            return self._t("corr_bajo_a").format(**datos)
        if c.nivel_antes is c.nivel_despues:  # el nivel no cambió: solo la razón de la línea tiene su propio texto
            clave = "corr_sin_linea" if c.razon is RazonCorreccion.LINEA_NO_CONFIRMADA else "corr_corregido"
            return self._t(clave).format(**datos)
        return self._t("corr_bajo").format(antes=NIVEL[c.nivel_antes][i].lower(), **datos)

    def autocomprobacion(self) -> None:
        """Aviso de la autocomprobación: qué es, cuál hallazgo cambió y a qué nivel (con más de 3, lista 3 y «y N más»)."""
        d = self.d
        if not d.correcciones and not d.hallazgos_corregidos:
            return
        self.termino(Termino.AUTOCOMPROBACION, 0, rol=None)
        if d.correcciones:
            avisos = [self._aviso_correccion(c) for c in d.correcciones]
            tope = len(avisos) if self.detalle else 3
            for aviso in avisos[:tope]:
                self.linea(aviso, 2, 4)
            if len(avisos) > tope:
                self.linea(self._t("corr_mas").format(n=len(avisos) - tope), 2, 2)
            if any(c.razon is RazonCorreccion.LINEA_NO_CONFIRMADA for c in d.correcciones):
                self.termino(Termino.LUGAR_NO_CONFIRMADO, 2, rol=None)
        else:  # sin los datos de cuál: el aviso de siempre, sin romperse
            self.linea(self._t("corr_generico").format(n=d.hallazgos_corregidos), 2, 2)
        self.linea()

    def reglas(self) -> None:
        d, i = self.d, self.i
        if not d.reglas and not d.limpieza_de_entorno and not d.esquemas:
            return
        self.linea(self._t("reglas_titulo", i))
        self.linea(self._t("reglas_intro", i))
        for plataforma in (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE):
            propias = [r for r in d.reglas if r.plataforma is plataforma]
            esquema = [e for p, e in d.esquemas if p is plataforma]
            if not propias and plataforma not in d.limpieza_de_entorno and not esquema:
                continue
            self.linea(_PLATAFORMA[plataforma], 2)
            for e in esquema:
                self.linea(self._t(f"esquema_{e}", i), 4, 6)
            for r in propias:
                self.linea(f"{POSTURA[r.postura][i]} · {r.herramienta} · {r.ubicacion}", 4, 6)
            if plataforma in d.limpieza_de_entorno:
                self.linea(self._t("limpieza", i), 4, 6)
        self.linea()

    def _nombre_plataforma(self, h: HallazgoVista) -> str:
        base = _PLATAFORMA.get(h.plataforma, self._t("no_determinada", self.i))
        if h.agente and h.agente not in ("sin-agente", "claude-code", "opencode"):
            base += f" ({h.agente})"
        return base

    def _reglas_de(self, h: HallazgoVista) -> str:
        texto = POSTURA[h.postura][self.i]
        if h.regla:
            texto += f" ({self._t('regla_en', self.i)} {h.regla})"
        return texto

    def hallazgos(self) -> None:
        d, i = self.d, self.i
        if not d.hallazgos:
            self.linea(f"{'[ok]' if self.ascii else '√'} {self._t('sin_hallazgos', i)}", rol="ok")
            self.linea(self._t("sin_hallazgos_frase", i))
            self.linea()
            return
        for plataforma, del_agente in self._secciones():
            titulo = self._titulo_seccion(plataforma)
            self.crudo(titulo)
            self.crudo("-" * ancho_visible(titulo))
            self.linea()
            for nivel, intro in ((Nivel.COMPROBADO, "intro_comprobado"), (Nivel.POTENCIAL, "intro_potencial"),
                                 (Nivel.HIPOTESIS, "intro_hipotesis")):
                grupo = [h for h in del_agente if h.nivel is nivel]
                if not grupo:
                    continue
                self.linea(f"{self.simbolo(nivel)} {NIVEL[nivel][i]} ({len(grupo)})", rol=_ROL_NIVEL[nivel])
                self.linea(self._t(intro, i))
                self.linea()
                for ruta in sorted({h.ruta for h in grupo}):
                    self.ruta(ruta)
                    vistos: dict[tuple, int | None] = {}
                    for h in sorted((x for x in grupo if x.ruta == ruta),
                                    key=lambda x: (x.linea is None, x.linea or 0, int(x.tipo.value.split("-")[1]))):
                        self._hallazgo(nivel, h, vistos)
                    self.linea()

    def configurados(self) -> None:
        """Los agentes configurados según el catálogo de firmas: «configurado», nunca «ejecutado»."""
        i, d = self.i, self.d
        if not d.configurados and not d.sin_decidir:
            return
        self.linea(self._t("cfg_titulo", i))
        if any(not c.marco and not c.analizado for c in d.configurados):  # la ficha ya dice que no es «se ejecutó»
            self.termino(Termino.CONFIGURADO_VS_ANALIZADO, 2, rol=None)
        else:
            self.linea(self._t("cfg_intro", i), 2, 2)
        for c in d.configurados:
            partes = [f"{c.nombre} · {self._t('cfg_' + {'high': 'high', 'potential': 'potential', 'hypothesis': 'hypothesis'}[c.confianza], i)}"]
            if c.marco:
                sobre = ", ".join(c.sobre) or self._t("cfg_un_agente", i)
                partes.append(self._t("cfg_marco", i).format(sobre=sobre))
            elif not c.analizado:
                partes.append(self._t("cfg_no_analiza", i))
            ambitos = _AMBITOS[i]
            cuenta = Counter(a for a, _ in c.evidencia)
            partes.append(", ".join(f"{ambitos[a]}: {n}" for a, n in cuenta.items()))
            self.linea(" — ".join(partes), 2, 4)
            if self.detalle:
                for ambito, ruta in c.evidencia:
                    self.crudo(f"      {ambitos[ambito]}: {ruta}")
        for r in d.sin_decidir:
            self.linea(self._t("cfg_indeterminado", i).format(ruta=r.ruta, candidatos=", ".join(r.candidatos)), 2, 4)
        self.linea()

    def no_determinado(self) -> None:
        """Por qué hay niveles «no determinado»: el archivo y la clave que AgentReach no interpreta, sin valores."""
        i, d = self.i, self.d
        afectados = {p: sum(1 for h in d.hallazgos if h.plataforma is p and h.motivo is Motivo.NO_DETERMINADO) for p in Plataforma}
        grupos = [(p, [c for c in d.causas if c.plataforma is p]) for p in (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE)]
        grupos = [(p, cs) for p, cs in grupos if afectados[p] and cs]
        if not grupos:
            return
        self.linea(self._t("nd_titulo", i))
        self.termino(Termino.NO_DETERMINADO, 2, rol=None)
        causas_todas = [c for _, cs in grupos for c in cs]
        if any(_es_hook(c) for c in causas_todas):  # una sola explicación de hook, aunque haya muchos hallazgos
            self.termino(Termino.HOOK, 2, rol=None)
            self.linea(punto_ciego(i, self.tono), 2, 2)
        motivos: list[MotivoNoRevisado] = []
        for plataforma, causas in grupos:
            self.linea(f"{_PLATAFORMA[plataforma]} ({self._t('nd_afecta', i).format(n=afectados[plataforma])})", 2)
            ultima = None
            for c in causas:
                if c.ruta != ultima:  # varias claves del mismo archivo comparten su línea de ruta
                    self.ruta(c.ruta, 4, rol="potencial")
                    ultima = c.ruta
                self.linea(self._causa_llana(c), 6, 6)  # la frase llana primero; la clave técnica, entre paréntesis después
                if c.motivo not in motivos:
                    motivos.append(c.motivo)
        flecha = "->" if self.ascii else "→"
        for motivo in motivos:
            self.linea(f"{flecha} {como_resolver(motivo, i, self.tono)}", 2, 4, rol="ok")
        self.linea()

    def _causa_llana(self, c) -> str:
        if c.motivo is MotivoNoRevisado.FUNCION_NO_MODELADA and _es_hook(c):
            frase = self._t("nd_hook")
        elif c.motivo is MotivoNoRevisado.FUNCION_NO_MODELADA and _es_sandbox(c):
            frase = self._t("nd_sandbox")
        else:
            frase = TITULO_MOTIVO[c.motivo][self.i]
        return f"{frase} ({c.clave})" if c.clave else frase

    def urgentes(self, cuantos: int = 3) -> None:
        """Lo más urgente: los primeros hallazgos por nivel (comprobado, potencial, hipótesis), de cualquier agente."""
        d, i = self.d, self.i
        if not d.hallazgos:
            self.linea(f"{'[ok]' if self.ascii else '√'} {self._t('sin_hallazgos', i)}", rol="ok")
            self.linea("No se encontró nada en lo que se pudo revisar." if i is Idioma.ES else "Nothing was found in what could be checked.")
            self.linea()
            return
        orden = sorted(d.hallazgos, key=lambda h: (h.nivel.prioridad, h.ruta, h.linea is None, h.linea or 0, int(h.tipo.value.split("-")[1])))
        elegidos = orden[:cuantos]
        self.linea(f"{self._t('urgentes', i)}  ({self._t('urgentes_de', i).format(n=len(elegidos), total=len(orden))})")
        for h in elegidos:
            titulo = titulo_corto(h.tipo, i)
            self.linea(f"{self.simbolo(h.nivel)} {NIVEL[h.nivel][i]} · {self._nombre_plataforma(h)} · {titulo}", 2, 4, rol=_ROL_NIVEL[h.nivel])
            self.ruta(h.ruta + (f":{h.linea}" if h.linea is not None else ""), 4)
            try:
                hacer = que_hacer(h.tipo, i, self.tono)
            except KeyError:  # sin «qué hacer» en el catálogo: se omite la línea
                hacer = ""
            if hacer:
                self.linea(f"{'->' if self.ascii else '→'} {hacer}", 4, 6, rol="ok")
        self.linea()

    def _secciones(self) -> list[tuple[Plataforma, list[HallazgoVista]]]:
        """Una sección por agente (Claude Code, opencode) y una para lo que no depende de uno. Los niveles no se mezclan."""
        orden = (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE, Plataforma.NO_DETERMINADA)
        secciones = [(p, [h for h in self.d.hallazgos if h.plataforma is p]) for p in orden]
        return [(p, grupo) for p, grupo in secciones if grupo]

    def _titulo_seccion(self, plataforma: Plataforma) -> str:
        if plataforma is Plataforma.NO_DETERMINADA:
            return self._t("seccion_general")
        return f"{self._t('seccion_agente')}: {_PLATAFORMA[plataforma]}"

    def _hallazgo(self, nivel: Nivel, h: HallazgoVista, vistos: dict[tuple, int | None]) -> None:
        i = self.i
        donde = f"{self._t('linea', i)} {h.linea}" if h.linea is not None else self._t("linea_nd", i)
        proveedor = PROVEEDOR[h.proveedor][i]
        titulo = titulo_corto(h.tipo, i) + (f" ({proveedor})" if proveedor else "")
        self.linea(f"{self.simbolo(nivel)} {donde} · {titulo}", 2, 4, rol=_ROL_NIVEL[nivel])
        motivo = texto_de_motivo(h.motivo, i)
        por_que = f"{self._t('nivel_y_por_que', i)}: {NIVEL[nivel][i].lower()}. {motivo}."
        ajeno = AJENO[h.ajeno][i]
        if self.detalle:
            self.etiquetada(f"{self._t('ubicacion', i)}:", h.ruta + (f":{h.linea}" if h.linea is not None else ""), 4)
            self.linea(f"{self._t('codigo_catalogo', i)}: {h.tipo.value}", 4, 6)
            self.linea(por_que, 4, 6)
            self.linea(f"{self._t('motivo_tecnico', i)}: {h.motivo.value}", 4, 6)
            self.linea(f"{self._t('plataforma', i)}: {self._nombre_plataforma(h)}", 4, 6)
            self.linea(f"{self._t('reglas', i)}: {self._reglas_de(h)}", 4, 6)
            self.linea(f"{self._t('ajeno', i)}: {ajeno}", 4, 6)
            self.linea(f"{self._t('fuente', i)}: {self._t('si' if h.fuente_verificada else 'no', i)}", 4, 6)
            self._explicacion(h)
            return
        self.linea(por_que, 4, 6)
        self.linea(f"{self._t('plataforma', i)}: {self._nombre_plataforma(h)} · {self._t('reglas', i)}: {self._reglas_de(h)} · "
                   f"{self._t('ajeno', i)}: {ajeno}", 4, 6)
        clave = (h.tipo, h.agente, h.motivo, h.ajeno)
        if vistos.get(clave) is not None:  # P7: el segundo del mismo tipo en el mismo archivo no repite la explicación
            self.linea(self._t("igual", i).format(n=vistos[clave]), 4, 6)
            return
        if h.linea is not None:
            vistos[clave] = h.linea
        self._explicacion(h)

    def _explicacion(self, h: HallazgoVista) -> None:
        i = self.i
        flecha = "->" if self.ascii else "→"
        self.linea(f"{flecha} {self._t('que_hacer', i)}: {que_hacer(h.tipo, i, self.tono)}", 4, 6, rol="ok")
        self.linea(f"{self._t('que_significa', i)}: {que_significa(h.tipo, h.ajeno, i, self.tono)}", 4, 6)

    def _presentes(self) -> list[Termino]:
        """Los términos que aparecen en ESTE reporte, en el orden del catálogo."""
        d = self.d
        hay: set[Termino] = {t for n, t in _TERMINO_NIVEL.items() if any(h.nivel is n for h in d.hallazgos)}
        nd = [c for c in d.causas if any(h.plataforma is c.plataforma and h.motivo is Motivo.NO_DETERMINADO for h in d.hallazgos)]
        if nd:
            hay.add(Termino.NO_DETERMINADO)
        if any(_es_hook(c) for c in nd):
            hay.add(Termino.HOOK)
        if any(_es_sandbox(c) for c in nd):
            hay.add(Termino.SANDBOX)
        if d.no_revisados:
            hay.add(Termino.NO_SE_PUDO_REVISAR)
        if any(not c.marco and not c.analizado for c in d.configurados):
            hay.add(Termino.CONFIGURADO_VS_ANALIZADO)
        if d.correcciones or d.hallazgos_corregidos:
            hay.add(Termino.AUTOCOMPROBACION)
        if any(c.razon is RazonCorreccion.LINEA_NO_CONFIRMADA for c in d.correcciones):
            hay.add(Termino.LUGAR_NO_CONFIRMADO)
        hay.add(Termino.CODIGO_DE_SALIDA)
        return [t for t in Termino if t in hay]

    def terminos(self) -> None:
        """``--detalle``: la explicación larga (qué es, qué significa, qué hacer) de los términos presentes."""
        i = self.i
        self.linea(self._t("terminos_titulo", i))
        etiquetas_ = etiquetas(i, self.tono)
        for termino in self._presentes():
            self.linea(nombre_de(termino, i), 2, 2)
            for etiqueta, texto in zip(etiquetas_, explicacion(termino, i, self.tono)):
                self.linea(f"{etiqueta}: {texto}", 4, 6)
        self.linea()

    def no_revisado(self) -> None:
        d, i = self.d, self.i
        self.linea(self._t("no_revisar_titulo", i))
        self.linea(self._t("parte_a", i))
        self.linea(self._t("parte_a_intro", i), 2, 2)
        if not d.no_revisados:
            self.linea(self._t("nada", i), 2, 2)
        por_motivo: dict[MotivoNoRevisado, list[str]] = {}
        for n in d.no_revisados:
            por_motivo.setdefault(n.motivo, []).append(n.ruta)
        for motivo in MotivoNoRevisado:
            rutas = sorted(set(por_motivo.get(motivo, ())))
            if not rutas:
                continue
            etiqueta = TITULO_MOTIVO[motivo][i] + (f" [{motivo.value}]" if self.detalle else "")
            self.linea(f"{'[-]' if self.ascii else '○'} {etiqueta} ({len(rutas)})", 2, 4, rol="no_revisar")
            for ruta in rutas:
                self.ruta(ruta, 4)
            flecha = "->" if self.ascii else "→"
            self.linea(f"{flecha} {self._t('como_resolver', i)}: {como_resolver(motivo, i, self.tono)}", 4, 6, rol="ok")
        self.linea()
        self.linea(self._t("parte_b", i))
        self.linea(self._t("parte_b_intro", i), 2, 2)
        for n, limite in enumerate(LIMITES[i], start=1):
            self.linea(f"{n}. {limite}", 2, 5)
        self.linea(LIMITES_TAMBIEN[i], 2, 2)
        self.linea()

    def cierre(self) -> None:
        d, i = self.d, self.i
        if d.codigo_de_salida == 0:
            palabras = self._t("salida_0", i)
        elif any(h.nivel is Nivel.COMPROBADO for h in d.hallazgos):
            palabras = self._t("salida_1", i)
        else:
            palabras = self._t("salida_1_estricto", i)
        self.linea(f"{self._t('cierre', i)}: {d.codigo_de_salida} ({palabras})")
        if self.corto:
            self.linea(self._t("pista_corta", i))
        elif not self.detalle:
            self.linea(self._t("pista", i))


def aviso_de_secretos(idioma: Idioma) -> str:
    """El aviso fijo de «no se muestran valores de secretos», sin el «(i)» (lo usa también el reporte HTML)."""
    return _T["aviso"][idioma].removeprefix("(i) ")


def _pasada(d: DatosReporte, idioma: Idioma, detalle: bool, ancho: int, simbolos: bool, forzar_nota: bool,
            tono: Tono = Tono.CERCANO, corto: bool = False) -> _Texto:
    t = _Texto(d, idioma, detalle, ancho, simbolos, forzar_nota, tono, corto)
    t.encabezado()
    t.resumen()
    t.configurados()
    t.no_determinado()
    if corto:  # resumen de la terminal: por nivel, lo más urgente y el alcance; el listado completo es --detalle
        t.urgentes()
        t.linea(t._t("alcance_corto", idioma), rol="info")
        t.linea()
        t.cierre()
        return t
    t.reglas()
    t.hallazgos()
    t.no_revisado()
    if detalle:
        t.terminos()
    t.cierre()
    return t


def generar(
    d: DatosReporte,
    idioma: Idioma = Idioma.ES,
    detalle: bool = False,
    ancho: int = 80,
    ascii_: bool = False,
    color: Color = Color.NINGUNO,
    fondo_claro: bool = False,
    simbolos_ascii: bool | None = None,
    tono: Tono = Tono.CERCANO,
    banner: list[str] | None = None,
    corto: bool = False,
) -> str:
    """El reporte como una sola cadena, listo para escribirse de una vez: completo, o con ``corto`` el resumen de la terminal
    (por nivel, lo más urgente y el alcance).

    ``ascii_`` pide solo ASCII (símbolos y sin tildes); ``simbolos_ascii`` cambia solo los símbolos (lo que se usa cuando
    la salida no es una terminal: UTF-8 con símbolos ASCII). El color se aplica después de ajustar, línea por línea.
    """
    simbolos = ascii_ if simbolos_ascii is None else (simbolos_ascii or ascii_)
    t = _pasada(d, idioma, detalle, ancho, simbolos, False, tono, corto)
    if t.cambio and not t.nota_de_nombres:  # la segunda barrera escribió algo: se repite con la nota
        t = _pasada(d, idioma, detalle, ancho, simbolos, True, tono, corto)
    lineas = list(banner or [])  # el banner ya viene pintado (o plano) y con su respaldo ASCII
    for linea, rol in t.salida:
        plana = _ascii(linea) if ascii_ else linea
        lineas.append(pintar(plana, rol, color, fondo_claro))
    return ultima_comprobacion("\n".join(lineas) + "\n")
