# utils/modules/informacion.py
# -*- coding: utf-8 -*-
"""
Módulo de información general:
- Qué eres
- Qué puedes hacer
- Cómo iniciar sesión
- Problemas con la contraseña

Expone UN SOLO disparador: INFO_RE
El handle decide la sub-intención y responde.
"""

import re
import unicodedata

# ------------------ Normalización básica ------------------
def _norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s

# ------------------ Subpatrones (no expuestos) ------------------
_SUB_QUE_ERES_RE = r"""
\b(
    (?:q|que)\s*e?res\?? |
    quien\s*eres\?? |
    que\s*(?:haces|sois)
)\b
"""

_SUB_QUE_PUEDES_RE = r"""
\b(
    que\s*(?:pueds|puedes|puedses)\s*(?:hace?r|aser)? |
    para\s*que\s*(?:sirves|sives|sirve) |
    cuales?\s*son\s*tus\s*(?:funciones|habilidades|opciones)
)\b
"""

_SUB_INICIO_RE = r"""
(?x)
\b(
    # Prefijo obligatorio: como / cuándo / que (con variantes)
    (?:
        (?:como|c[oó]mo|kmo|komo) |
        (?:cuando|cu[aá]ndo|kuando|kndo) |
        (?:que|qu[eé]|k[eé])
    )
    \s+
    # Auxiliar opcional
    (?:puedo|podria|podr[ií]a|debo|necesito|quiero)? \s*
    # Verbo de acceso (con errores comunes)
    (?:
        iniciar|inciar|inicio|inicar|iniiar|
        entrar|ingresar|
        acceder|aceder|
        log(?:in)?|loguear(?:me|se)?|
        meterme|abrir|acceso
    )
    # Objeto destino opcional
    (?:\s+(?:a\s+)?(?:mi\s+)?(?:cuenta|usuario|sesion|session|secion|seson|sistema))?
)\b
"""

_SUB_PASS_PROB_RE = r"""
\b(
    (?:problema|error|olvide|olvid[ée]|cambio|restaurar|recuperar|resetear)\s+
    (?:mi\s*)?(?:clave|password|pass|contrasen?a|contrase(?:n|ñ)a|cotrasena)
)\b
"""

# ------------------ ÚNICO disparador público ------------------
INFO_RE = rf"""
(?x)
(?:{_SUB_QUE_ERES_RE}) |
(?:{_SUB_QUE_PUEDES_RE}) |
(?:{_SUB_INICIO_RE}) |
(?:{_SUB_PASS_PROB_RE})
"""

# ------------------ Handler ------------------
def handle(ctx, text: str) -> str:
    t = _norm(text)

    # Compilaciones para detección fina
    rx_eres   = re.compile(_SUB_QUE_ERES_RE,   re.I | re.X)
    rx_puedes = re.compile(_SUB_QUE_PUEDES_RE, re.I | re.X)
    rx_inicio = re.compile(_SUB_INICIO_RE,     re.I | re.X)
    rx_pass   = re.compile(_SUB_PASS_PROB_RE,  re.I | re.X)

    # 1) Qué eres
    if rx_eres.search(t):
        return (
            "Soy un asistente del SAES que entiende comandos comunes y con errores "
            "de ortografía. Te ayudo con: inicio/cierre de sesión, info académica, materias, "
            "trámites, inscripción y consultas rápidas.\n\n"
            "Prueba: '¿qué puedes hacer?', 'iniciar sesión', 'problemas con mi contraseña'."
        )

    # 2) Qué puedes hacer
    if rx_puedes.search(t):
        return (
            "Puedo ayudarte a:\n"
            "• Iniciar sesión y cerrar sesión.\n"
            "• Ver info académica, materias, grupos y cupos.\n"
            "• Consultar calificaciones.\n"
            "• Orientarte en trámites e inscripción.\n\n"
            "Comandos de ejemplo:\n"
            "• 'iniciar sesion'\n"
            "• 'ver materias'\n"
            "• 'info academica'\n"
            "• 'tramites' o 'inscripcion'\n"
            "• 'problemas con mi contraseña'"
        )

    # 3) Cómo iniciar sesión
    if rx_inicio.search(t):
        # Aquí SOLO informamos el flujo, NO hacemos login real.
        return (
            "Para iniciar sesión:\n"
            "1) Di: 'iniciar sesion' (o 'entrar', 'login').\n"
            "2) Cuando te pida el usuario, responde: 'mi usuario es 2023630011'.\n"
            "3) Luego la contraseña: 'mi contrasena es 1234'.\n\n"
            "Si ya estás dentro, podrás pedir 'materias', 'info academica', 'tramites' o 'inscripcion'."
        )

    # 4) Problemas con contraseña
    if rx_pass.search(t):
        return (
            "Si olvidaste o tienes problemas con tu contraseña:\n"
            "• Intenta: 'recuperar contrasena' o 'resetear contrasena'.\n"
            "• Te pediremos tu boleta/usuario y un correo para verificación.\n"
            "• Si no funciona, contacta a servicios escolares para restablecimiento manual.\n\n"
            "Mientras tanto, puedes volver a intentar inicio: 'iniciar sesion'."
        )

    # Fallback (si por alguna razón el disparador coincidió pero no un submatch)
    return (
        "¿Qué necesitas saber? Puedo explicarte qué soy, qué puedo hacer, cómo iniciar sesión "
        "o cómo recuperar tu contraseña."
    )

# Si quieres mantenerte en el mismo estado después de responder:
# NEXT_STATE = "START"


NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK"}
