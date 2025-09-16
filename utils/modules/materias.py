# utils/modules/materias.py
MATERIAS_RE = r"\b(materia(?:s)?|lista\s+de\s+materias|ver\s+materias|grupos|cupos?)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    # Simulación
    return ("Materias disponibles (ejemplo): Cálculo, Programación, Redes. "
            "Di 'inscripcion' para inscribirte o 'ver calificaciones'.")

NEXT_STATE = "MATERIAS"
ALLOWED_STATES = {"AUTH_OK", "MATERIAS"}
