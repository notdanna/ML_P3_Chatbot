import re, unicodedata

# Estado siguiente opcional (lo leerá el autómata si lo defines)
NEXT_STATE = "AUTH"

def handle(ctx, text):
    # Aquí va la lógica real de login (pedir/parsear matrícula y password, etc.)
    # Por ahora, una respuesta de demo:
    return "Vamos a iniciar sesión (demo). Escribe: 'iniciar sesión <matrícula> <password>'."

# Inicializacion
Iniciar_Sesion_RE = r"""
(?i)\b(
    iniciar\s+sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign\s*in | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes
)\b
"""
