import re

LOGIN_RE = r"\b(iniciar\s+sesion|login)\b"

# Permite letras, números, punto, guion y guion bajo
USER_RE  = r"\bmi\s+usuario\s+es\s+([A-Za-z0-9._-]+)\b"
Iniciar_Sesion_RE = r"""
(?i)\b(
    iniciar\s+sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign\s*in | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes | hola
)\b
"""

def handle(ctx, text):
    # Si ya tenemos usuario, seguimos el flujo
    if ctx.get("user"):
        return f"Ya tengo tu usuario '{ctx['user']}'. Dime tu contraseña."

    m = re.search(USER_RE, text, re.I)
    if m:
        ctx["user"] = m.group(1)  # <-- ajustado al nuevo grupo
        return f"Usuario '{ctx['user']}' guardado. Ahora dime tu contraseña."

    return "Ok, dime tu usuario (ej: 'mi usuario es miguel')."

NEXT_STATE = "AUTH"
ALLOWED_STATES = {"START", "AUTH"}  

