# utils/modules/cerrarSesion.py
SALIR_RE = r"\b(cerrar\s+sesion|logout|salir|terminar)\b"

def handle(ctx, text):
    ctx.clear()
    ctx["state"] = "START"
    # si usas atributo:
    try:
        ctx.state = "START"
    except Exception:
        pass
    return "Sesión cerrada. Escribe 'iniciar sesion' para entrar de nuevo."

NEXT_STATE = "END"
ALLOWED_STATES = None   # disponible siempre
