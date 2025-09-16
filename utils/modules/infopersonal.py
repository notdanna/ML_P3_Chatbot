# utils/modules/infopersonal.py
INFOPER_RE = r"\b(info\s+personal|datos\s+personales|informacion\s+personal|medica)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    # Simulación
    return ("Info personal: Nombre completo en sistema, NSS, correo institucional... "
            "¿Deseas 'info academica', 'materias', 'tramites' o 'inscripcion'?")

NEXT_STATE = "INFO_PERSONAL"
ALLOWED_STATES = {"AUTH_OK", "INFO_PERSONAL"}
