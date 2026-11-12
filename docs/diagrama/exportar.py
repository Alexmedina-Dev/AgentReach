"""Exporta Diagram.dc.html a ../../assets/agentreach-arquitectura.png.

Uso (desde cualquier carpeta):
    uv run --no-project --with playwright python docs/diagrama/exportar.py

Requiere Microsoft Edge instalado. Se renderiza con JavaScript desactivado:
el diseño es HTML y CSS estáticos.
"""
import pathlib
from playwright.sync_api import sync_playwright

aqui = pathlib.Path(__file__).resolve().parent
salida = aqui.parent.parent / "assets" / "agentreach-arquitectura.png"

with sync_playwright() as p:
    navegador = p.chromium.launch(channel="msedge", headless=True)
    contexto = navegador.new_context(
        viewport={"width": 1600, "height": 900},
        device_scale_factor=2,
        java_script_enabled=False,
    )
    pagina = contexto.new_page()
    pagina.goto((aqui / "Diagram.dc.html").as_uri())
    pagina.wait_for_timeout(2500)  # fuentes de Google Fonts
    pagina.screenshot(path=str(salida))
    navegador.close()
print("OK:", salida)
