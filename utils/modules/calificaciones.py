# utils/modules/calificaciones.py
CALIF_RE = r"\b(calificacion(?:es)?|boleta|ver\s+calificacion(?:es)?)\b"

def handle(ctx, text):
    if not ctx.get("user"):
        return "Primero inicia sesión."
    if not ctx.get("auth_ok"):             # ← exige que ya haya contraseña
        return "Dime tu contraseña primero."
    return "Tus calificaciones: Álgebra 9, Cálculo 8, Programación 10. ¿Quieres 'info académica'?"

NEXT_STATE = "CALIFICACIONES"
ALLOWED_STATES = {"AUTH_OK"}
