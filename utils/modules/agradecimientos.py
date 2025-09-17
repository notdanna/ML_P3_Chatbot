# utils/modules/infopersonal.py

# Todas las posibles gracias y todos agradecimientos
AGRADECIMIENTOS_RE = r"\b(gracias|muchas gracias|te lo agradezco|muy amable|gracias por tu ayuda|gracias por la informacion|tenkiu|thank you|gracias por la info)\b"

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "De nada uwu"
    # Simulación
    return ("De nada uwu")

NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
