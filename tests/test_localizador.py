"""Pruebas del localizador de claves (línea y columna), con pytest.

Todos los "secretos" de estas pruebas son datos falsos.
"""

from pathlib import Path

import pytest

from agentreach.infra.localizador import localizar_clave, localizar_posicion

OPENCODE = (
    "{\n"
    '  "$schema": "https://opencode.ai/config.json",\n'
    '  "permission": {\n'
    '    "read": "allow",\n'
    '    "edit": "allow",\n'
    '    "bash": "allow",\n'
    '    "webfetch": "allow",\n'
    '    "external_directory": "ask"\n'
    "  }\n"
    "}\n"
)

CLAUDE_SETTINGS = """{
  // permisos del proyecto (comentario estilo JSONC)
  "permissions": {
    "allow": ["Read(./src/**)"],

    /* reglas de bloqueo */
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)",
    ],
  },
}
"""


# --- JSON ---------------------------------------------------------------------------------


def test_json_claves_anidadas_opencode():
    assert localizar_clave(OPENCODE, "json", ("permission",)) == 3
    assert localizar_clave(OPENCODE, "json", ("permission", "read")) == 4
    assert localizar_clave(OPENCODE, "json", ("permission", "bash")) == 6
    assert localizar_clave(OPENCODE, "json", ("permission", "external_directory")) == 8


def test_json_columna():
    assert localizar_posicion(OPENCODE, "json", ("permission", "bash")) == (6, 5)
    assert localizar_posicion(OPENCODE, "json", ("permission",)) == (3, 3)


def test_json_arreglo_de_reglas_con_comentarios_y_comas_finales():
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "allow")) == 4
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "allow", 0)) == 4
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny")) == 7
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny", 0)) == 8
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny", 1)) == 9


def test_json_comentario_que_parece_clave_no_cuenta():
    texto = '{\n  // "bash": "allow",\n  /* "bash": 1 */\n  "bash": "ask"\n}'
    assert localizar_clave(texto, "jsonc", ("bash",)) == 4


def test_json_cadena_con_comillas_escapadas_y_llaves():
    texto = '{\n  "a": "x\\" , } ] y",\n  "b": 1\n}'
    assert localizar_clave(texto, "json", ("b",)) == 3


def test_json_clave_con_escape_unicode():
    texto = '{\n  "\\u0061b": 1\n}'
    assert localizar_clave(texto, "json", ("ab",)) == 2


def test_json_lf_y_crlf_dan_la_misma_linea():
    lf = CLAUDE_SETTINGS
    crlf = CLAUDE_SETTINGS.replace("\n", "\r\n")
    for ruta in [("permissions", "deny", 1), ("permissions", "allow")]:
        assert localizar_posicion(lf, "jsonc", ruta) == localizar_posicion(crlf, "jsonc", ruta)
    assert localizar_clave(crlf, "jsonc", ("permissions", "deny", 1)) == 9


def test_json_con_marca_de_orden_de_bytes():
    assert localizar_posicion("\ufeff" + OPENCODE, "json", ("permission",)) == (3, 3)


def test_json_none_si_no_existe():
    assert localizar_clave(OPENCODE, "json", ("permission", "nada")) is None
    assert localizar_clave(OPENCODE, "json", ("otra",)) is None
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny", 5)) is None
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny", -1)) is None


def test_json_none_si_el_tipo_no_coincide():
    assert localizar_clave(OPENCODE, "json", ("permission", "read", "x")) is None  # valor simple
    assert localizar_clave(OPENCODE, "json", ("permission", 0)) is None  # objeto, no arreglo
    assert localizar_clave(CLAUDE_SETTINGS, "jsonc", ("permissions", "deny", "x")) is None


def test_json_none_si_esta_mal_formado():
    assert localizar_clave('{"a": 1,, "b": 2}', "json", ("b",)) is None
    assert localizar_clave('{"a": 1', "json", ("a",)) is None
    assert localizar_clave('{"a": 1} basura', "json", ("a",)) is None
    assert localizar_clave('{"a": /* sin cerrar }', "jsonc", ("a",)) is None
    assert localizar_clave("", "json", ("a",)) is None


def test_json_none_si_la_clave_esta_repetida():
    assert localizar_clave('{\n"a": 1,\n"a": 2\n}', "json", ("a",)) is None


def test_json_none_con_ruta_vacia_o_pasos_invalidos():
    assert localizar_clave(OPENCODE, "json", ()) is None
    assert localizar_clave(OPENCODE, "json", (True,)) is None  # type: ignore[arg-type]


def test_json_profundidad_excesiva_devuelve_none():
    texto = "[" * 500 + "]" * 500
    assert localizar_clave(texto, "json", (0,)) is None


def test_opencode_real_del_proyecto_de_prueba_si_existe():
    ruta = Path(r"C:\dev\proyecto-prueba-agentreach\proyecto\opencode.json")
    if not ruta.is_file():
        pytest.skip("No está el proyecto de prueba en esta máquina.")
    texto = ruta.read_text(encoding="utf-8")
    assert localizar_clave(texto, "json", ("permission", "bash")) == 6


# --- .env ---------------------------------------------------------------------------------

ENV = (
    "# Secreto FALSO con permisos demasiado abiertos\n"
    "EXPORT_SECRET=valor-falso-123\n"
    "\n"
    "   # otro comentario\n"
    "export SERVICE_TOKEN = 'falso'\n"
    "# COMENTADA=1\n"
    "MULTI=\"linea uno\n"
    "FALSA_CLAVE_DENTRO=2\n"
    'fin"\n'
    "DESPUES=1\n"
)


def test_env_nombre_y_linea():
    assert localizar_clave(ENV, "env", ("EXPORT_SECRET",)) == 2
    assert localizar_posicion(ENV, "env", ("EXPORT_SECRET",)) == (2, 1)


def test_env_export_y_espacios():
    assert localizar_posicion(ENV, "env", ("SERVICE_TOKEN",)) == (5, 8)


def test_env_ignora_comentarios_y_valores_multilinea():
    assert localizar_clave(ENV, "env", ("COMENTADA",)) is None
    assert localizar_clave(ENV, "env", ("FALSA_CLAVE_DENTRO",)) is None
    assert localizar_clave(ENV, "env", ("MULTI",)) == 7
    assert localizar_clave(ENV, "env", ("DESPUES",)) == 10


def test_env_crlf():
    assert localizar_clave(ENV.replace("\n", "\r\n"), "env", ("DESPUES",)) == 10


def test_env_none_si_no_existe_repetida_o_ruta_invalida():
    assert localizar_clave(ENV, "env", ("NO_EXISTE",)) is None
    assert localizar_clave("A=1\nA=2\n", "env", ("A",)) is None
    assert localizar_clave(ENV, "env", ("EXPORT_SECRET", "x")) is None
    assert localizar_clave(ENV, "env", (0,)) is None
    assert localizar_clave('A="sin cerrar\n', "env", ("A",)) is None


def test_env_nombre_sin_igual_no_cuenta():
    assert localizar_clave("SOLO_NOMBRE\nB=1\n", "env", ("SOLO_NOMBRE",)) is None


# --- TOML ---------------------------------------------------------------------------------

TOML = '''# configuración de ejemplo
titulo = "x"

[servidor]
host = "localhost"   # comentario
"puerto raro" = 8080
a.b.c = 1

[servidor.tls]
activo = true
nota = """
linea falsa = 1
[no_es_tabla]
"""

[[reglas]]
nombre = "uno"

[[reglas]]
nombre = "dos"
patrones = [
  "a",   # [no_tabla]
  "b",
]

[[reglas.sub]]
x = 1

[[reglas]]
nombre = "tres"
'''


def test_toml_claves_y_tablas():
    assert localizar_clave(TOML, "toml", ("titulo",)) == 2
    assert localizar_clave(TOML, "toml", ("servidor",)) == 4
    assert localizar_clave(TOML, "toml", ("servidor", "host")) == 5
    assert localizar_posicion(TOML, "toml", ("servidor", "host")) == (5, 1)
    assert localizar_clave(TOML, "toml", ("servidor", "tls")) == 9
    assert localizar_clave(TOML, "toml", ("servidor", "tls", "activo")) == 10


def test_toml_clave_entre_comillas_y_con_puntos():
    assert localizar_clave(TOML, "toml", ("servidor", "puerto raro")) == 6
    assert localizar_clave(TOML, "toml", ("servidor", "a", "b", "c")) == 7


def test_toml_no_se_deja_enganar_por_cadenas_multilinea_ni_comentarios():
    assert localizar_clave(TOML, "toml", ("no_es_tabla",)) is None
    assert localizar_clave(TOML, "toml", ("no_tabla",)) is None
    assert localizar_clave(TOML, "toml", ("linea falsa",)) is None


def test_toml_arreglo_de_tablas_por_indice():
    assert localizar_clave(TOML, "toml", ("reglas", 0)) == 16
    assert localizar_clave(TOML, "toml", ("reglas", 0, "nombre")) == 17
    assert localizar_clave(TOML, "toml", ("reglas", 1, "nombre")) == 20
    assert localizar_clave(TOML, "toml", ("reglas", 1, "patrones")) == 21
    assert localizar_clave(TOML, "toml", ("reglas", 1, "sub", 0, "x")) == 27
    assert localizar_clave(TOML, "toml", ("reglas", 2, "nombre")) == 30
    assert localizar_clave(TOML, "toml", ("reglas", 3)) is None


def test_toml_lf_y_crlf():
    crlf = TOML.replace("\n", "\r\n")
    assert localizar_clave(crlf, "toml", ("reglas", 2, "nombre")) == 30
    assert localizar_clave(crlf, "toml", ("servidor", "tls", "activo")) == 10


def test_toml_limites_documentados_devuelven_none():
    inline = 'a = { b = 1 }\nc = [1, 2]\n'
    assert localizar_clave(inline, "toml", ("a",)) == 1
    assert localizar_clave(inline, "toml", ("a", "b")) is None  # dentro de tabla en línea
    assert localizar_clave(inline, "toml", ("c", 0)) is None  # dentro de arreglo en línea
    assert localizar_clave(TOML, "toml", ("servidor", "a")) is None  # tabla implícita


def test_toml_none_si_repetida_ausente_o_mal_formada():
    assert localizar_clave("a = 1\na = 2\n", "toml", ("a",)) is None
    assert localizar_clave("a = 1\n", "toml", ("b",)) is None
    assert localizar_clave("a = \n", "toml", ("a",)) is None
    assert localizar_clave("a = 1 basura\n", "toml", ("a",)) is None
    assert localizar_clave('a = """sin cerrar\n', "toml", ("a",)) is None
    assert localizar_clave("[tabla\nx = 1\n", "toml", ("x",)) is None


# --- General ------------------------------------------------------------------------------


def test_formato_desconocido_es_error_de_programacion():
    with pytest.raises(ValueError):
        localizar_clave("a: 1", "yaml", ("a",))


def test_el_resultado_nunca_contiene_el_valor():
    for texto, formato, ruta in [
        (ENV, "env", ("EXPORT_SECRET",)),
        ('{"token": "valor-falso-123"}', "json", ("token",)),
        ('token = "valor-falso-123"', "toml", ("token",)),
    ]:
        resultado = localizar_posicion(texto, formato, ruta)
        assert resultado is not None
        assert all(isinstance(x, int) for x in resultado)
