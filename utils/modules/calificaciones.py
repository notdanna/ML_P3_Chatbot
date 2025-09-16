# utils/modules/calificaciones.py
CALIF_RE = r"\b(calificacion(?:es)?|boleta|ver\s+calificacion(?:es)?)\b"

def handle(ctx, text):
    if not ctx.get("user"):
        return "Primero inicia sesión."
    if not ctx.get("auth_ok"):
        return "Dime tu contraseña primero."
    # Simulación
    user = ctx.get("user", "alumno")
    return (f"Tus calificaciones, {user}: Álgebra 9, Cálculo 8, Programación 10. "
            "¿Quieres 'info academica', 'materias', 'tramites' o 'inscripcion'?")

NEXT_STATE = "CALIFICACIONES"
ALLOWED_STATES = {"AUTH_OK", "CALIFICACIONES"}
