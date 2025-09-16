# utils/modules/infoacademica.py
INFOACAD_RE = r"\b(info(\s+academica)?|kardex|historial\s+academico)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    # Simulación
    return ("Info académica: Carrera ISC, Semestre 6, Promedio 9.1. "
            "Puedes pedir 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'.")

NEXT_STATE = "INFO_ACADEMICA"
ALLOWED_STATES = {"AUTH_OK", "INFO_ACADEMICA", "CALIFICACIONES"}
