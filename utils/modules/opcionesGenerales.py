# utils/modules/opcionesGenerales.py
OPCIONES_RE = r"\b(opciones|menu|ayuda|que\s+puedo\s+hacer)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return ("Opciones básicas: 'iniciar sesion'. Luego podrás pedir "
                "'ver calificaciones', 'info academica', 'info personal', "
                "'materias', 'tramites' o 'inscripcion'.")
    return ("Opciones: 'ver calificaciones', 'info academica', 'info personal', "
            "'materias', 'tramites', 'inscripcion', 'cerrar sesion'.")

NEXT_STATE = "AUTH_OK"  # Mantener el estado de autenticado
ALLOWED_STATES = {"AUTH_OK"}  # Solo necesita estar autenticado