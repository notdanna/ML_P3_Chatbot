# utils/modules/inscripcion.py
INSCRIP_RE = r"\b(inscripcion|inscribirme|inscribir|seleccion\s+de\s+(turno|grupo))\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    return ("Inscripción: di 'materias' para ver oferta, o 'seleccionar grupo <CLAVE>' "
            "(lógica a implementar). También puedes pedir 'ver calificaciones'.")

NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
