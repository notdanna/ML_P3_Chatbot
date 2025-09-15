# utils/modules/contrasena.py
# Acepta cualquier token no vacío como "contraseña" (ajústalo a tu gusto)
PASS_RE = r"^\s*([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\s*$"

def handle(ctx, text):
    if not ctx.get("user"):
        return "Primero dime tu usuario: 'mi usuario es <usuario>'."
    # Guarda y marca autenticado
    ctx["auth_ok"] = True
    # (si no quieres guardar la contraseña, no lo hagas; aquí solo simulamos)
    return "Contraseña recibida. ¿Qué deseas? Puedes decir 'ver calificaciones'."

NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH"}    # solo cuando estamos en AUTH
