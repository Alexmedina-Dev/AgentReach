"""Patrones por NOMBRE de variable y por forma del valor. Nunca guardan un valor.

Reglas:
- Un nombre se reconoce por su texto (``STRIPE_SECRET_KEY``), no por lo que contiene el valor.
- Del valor solo se pregunta, de paso y sin conservarlo, si es de relleno (``changeme``, vacío,
  ``localhost``, ``EXAMPLE``) o una referencia (``${{ secrets.X }}``, ``os.environ[...]``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agentreach.contracts import Proveedor


@dataclass(frozen=True, slots=True)
class Clasificacion:
    proveedor: Proveedor
    alto_poder: bool  # token de plataforma o de despliegue (TH-17 fuera de un .env)


_GENERICO = re.compile(
    r"SECRET|TOKEN|PASSW(?:OR)?D|API_?KEY|PRIVATE_?KEY|ACCESS_?KEY|CREDENTIALS?|DATABASE_URL|DB_URL"
    r"|CONNECTION_STRING|_KEY$|PASS(?:WORD|WD)?(?:_|$)|_URI$",
    re.IGNORECASE,
)

_DESPLIEGUE = r"RAILWAY|VERCEL|NETLIFY|HEROKU|(?:^|_)FLY(?:_|$)|RENDER_|DIGITALOCEAN|CLOUDFLARE"

# Orden importa: gana el primero que coincide.
_PROVEEDORES: tuple[tuple[re.Pattern[str], Proveedor], ...] = (
    (re.compile(r"ANTHROPIC|OPENAI|GEMINI|MISTRAL|COHERE|GROQ|OPENROUTER|HUGGINGFACE|HF_", re.IGNORECASE), Proveedor.IA),
    (re.compile(r"STRIPE|PAYPAL|ADYEN|MERCADOPAGO|BRAINTREE", re.IGNORECASE), Proveedor.PAGOS),
    (re.compile(r"GITHUB|GITLAB|BITBUCKET|NPM_|NPM$", re.IGNORECASE), Proveedor.CODIGO),
    (re.compile(_DESPLIEGUE, re.IGNORECASE), Proveedor.DESPLIEGUE),
    (re.compile(r"AWS_|AZURE_|GCP_|GOOGLE_APPLICATION", re.IGNORECASE), Proveedor.NUBE),
    (re.compile(r"(?:^|_)DATABASE_(?:URL|URI|DSN|PASS|PASSWORD|USER)|DB_URL|(?:^|_)DB_(?:PASS|PASSWORD|USER)(?:_|$)|MONGO|POSTGRES|MYSQL|REDIS|CONNECTION_STRING", re.IGNORECASE), Proveedor.BASE_DE_DATOS),
    (re.compile(r"JWT|SIGNING|SESSION_SECRET|SECRET_KEY_BASE|HMAC", re.IGNORECASE), Proveedor.FIRMA),
)
_ALTO_PODER = re.compile(rf"(?:{_DESPLIEGUE}).*(?:TOKEN|KEY|SECRET)", re.IGNORECASE)


def clasificar_nombre(nombre: str) -> Clasificacion | None:
    """``None`` si el nombre no parece una credencial."""
    if not _GENERICO.search(nombre):
        return None
    proveedor = next((p for patron, p in _PROVEEDORES if patron.search(nombre)), Proveedor.DESCONOCIDO)
    return Clasificacion(proveedor, bool(_ALTO_PODER.search(nombre)))


_RELLENO = re.compile(
    r"^change[-_ ]?me|placeholder|^your[-_ ]|^<.*>$|^x{3,}$|^\*{3,}$|^todo|^replace|^dummy"
    r"|^(?:example|ejemplo)[-_a-z0-9]*$|^(?:token|secret|password|key|null|none|undefined|true|false)$"
    r"|^\d+$",
    re.IGNORECASE,
)
# Las claves de ejemplo de la documentación de los proveedores llevan EXAMPLE en mayúsculas.
# Una palabra "ejemplo" suelta en minúscula (p. ej. dentro de un host) no es relleno.
_EJEMPLO_DOC = re.compile(r"EXAMPLE")
_ANFITRION_LOCAL = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1"}
_REFERENCIA = re.compile(
    r"^\s*[\"']?(?:\$\{|\$\(|\$[A-Za-z_]|%[A-Za-z_]+%|os\.|process\.|env\.|getenv|secrets\.|vars\.|\{\{)",
    re.IGNORECASE,
)


def _es_local(valor: str) -> bool:
    """Solo mira el anfitrión: una clave real nunca se descarta por contener "localhost"."""
    if "://" in valor:
        resto = valor.split("://", 1)[1].split("/", 1)[0].rsplit("@", 1)[-1]
        anfitrion = resto.rsplit(":", 1)[0] if not resto.startswith("[") else resto.split("]")[0] + "]"
        return anfitrion.lower() in _ANFITRION_LOCAL
    anfitrion = valor.rsplit(":", 1)[0] if valor.count(":") == 1 else valor
    return anfitrion.lower() in _ANFITRION_LOCAL


def valor_es_relleno(valor: str) -> bool:
    """Vacío, de relleno o apuntando a la máquina local. No guarda ni devuelve el valor."""
    limpio = valor.strip().strip("\"'").strip()
    if not limpio or limpio.startswith("#"):
        return True
    return bool(_RELLENO.search(limpio) or _EJEMPLO_DOC.search(limpio) or _es_local(limpio))


def valor_es_referencia(valor: str) -> bool:
    """Referencia a otra fuente (variable, secreto del repositorio), no un valor literal."""
    return bool(_REFERENCIA.search(valor))
