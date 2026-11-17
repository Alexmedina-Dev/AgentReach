"""Historia 47: el texto de «archivo demasiado grande» dice el tope real, no un número escrito a mano.

El recorrido del proyecto no abre archivos de más de ``LIMITE_BYTES`` (1 MiB); el catálogo decía «más de 5 MB» y con eso
la persona no sabía por qué un archivo de 2 MB salía como «no se pudo revisar».
"""

from __future__ import annotations

from agentreach.contracts import LIMITE_BYTES, Idioma, MotivoNoRevisado
from agentreach.core.catalogo_explicaciones import TITULO_MOTIVO


def test_el_titulo_dice_el_tope_real_en_los_dos_idiomas():
    mb = LIMITE_BYTES // (1024 * 1024)
    for idioma in (Idioma.ES, Idioma.EN):
        texto = TITULO_MOTIVO[MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE][idioma]
        assert f"{mb} MB" in texto, texto
        assert "5 MB" not in texto, texto


def test_el_tope_es_el_del_recorrido_y_no_otro_numero_suelto():
    assert LIMITE_BYTES == 1024 * 1024  # si el tope cambia, el texto lo sigue solo; esta prueba obliga a decidirlo a propósito
