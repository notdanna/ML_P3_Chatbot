# utils/modules/opcionesGenerales.py
OPCIONES_RE = r"\b(opciones|menu|ayuda|que\s+puedo\s+hacer)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return ("Opciones básicas: 'iniciar sesion'. Luego podrás pedir "
                "'ver calificaciones', 'info academica', 'info personal', "
                "'materias', 'tramites' o 'inscripcion'.")
    return ("Opciones: 'ver calificaciones', 'info academica', 'info personal', "
            "'materias', 'tramites', 'inscripcion', 'cerrar sesion'.")

NEXT_STATE = ""          # no mover el estado
ALLOWED_STATES = None    # disponible en cualquier estado
