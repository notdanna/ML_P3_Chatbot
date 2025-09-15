import re
def handle(ctx, text):
    ctx.clear()
    return "Sesión cerrada."
Cerrar_Sesion_RE = r"""
(?i)\b(
    cerrar\s+sesion | terminar\s+sesion | salir | logout | sign\s*out |
    desconectar(?:me|se)? | cerrar\s+cuenta
)\b
"""
