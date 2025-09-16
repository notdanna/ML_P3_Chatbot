# utils/modules/inicioInfo.py
INICIOINFO_RE = r"\b(inicio\s*info|informacion\s+inicial|bienvenida)\b"

def handle(ctx, text):
    if ctx.get("auth_ok"):
        return ("Ya estás adentro. Pide: 'ver calificaciones', 'info academica', "
                "'info personal', 'materias', 'tramites', 'inscripcion' u 'opciones'.")
    return "Para comenzar, di: 'iniciar sesion'."

NEXT_STATE = ""                # no fuerza cambio
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK"}
