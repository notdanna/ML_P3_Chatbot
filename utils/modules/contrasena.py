# utils/modules/contrasena.py
"""
Este módulo no registra rutas. La contraseña se gestiona en iniciarSesion.py
Deja este archivo sin *_RE para no interferir.
"""
def handle(ctx, text):
    return "La contraseña se gestiona en 'iniciar sesion'."
# Sin NEXT_STATE, sin ALLOWED_STATES y sin *_RE → no se registra.
