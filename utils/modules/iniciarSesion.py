# utils/modules/iniciarSesion.py
import re

# 1) Disparadores de "iniciar sesión" (tolerantes; sin acentos porque el router normaliza)
LOGIN_RE = r"""
\b(
    iniciar\s*sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign\s*in | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes | hola
)\b
"""

# 2) Usuario: permite letras/números . _ - y espacios internos (ej: "ana perez")
USER_RE = r"\bmi\s+usuario\s+es\s+([A-Za-z0-9._-]+(?:\s+[A-Za-z0-9._-]+)*)\b"

# 3) Contraseña: dos formas de entrada
#    a) Solo el token en toda la línea (ej: "1234" o "Pa$$2025")
PASS_TOKEN_RE = r"^\s*([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\s*$"
#    b) Frase "mi contrasena es <token>" (sin tilde porque el router quita acentos)
PASS_SENTENCE_RE = r"\bmi\s+contrasena\s+es\s+([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\b"

def _render_calificaciones(ctx) -> str:
    # Simulación de calificaciones; aquí iría tu consulta real
    # Puedes usar ctx["user"] si quieres personalizar la salida
    return "Tus calificaciones: Álgebra 9, Cálculo 8, Programación 10. ¿Quieres 'info académica'?"

def handle(ctx, text):
    """
    Flujo en un solo handler:
      START → (login/usuario) → AUTH → (contrasena) → CALIFICACIONES (muestra boleta)
    - Si no hay usuario => intenta extraerlo; si no, lo pide y pone state=AUTH.
    - Si hay usuario y no hay auth_ok => intenta extraer contrasena; si no, la pide.
    - Si ya auth_ok => muestra calificaciones (idempotente).
    """
    # 0) Normaliza flags en contexto
    user = ctx.get("user")
    auth_ok = ctx.get("auth_ok", False)

    # 1) Si aún no tengo usuario
    if not user:
        m_user = re.search(USER_RE, text, re.I | re.X)
        if m_user:
            user = m_user.group(1)
            ctx["user"] = user
            # Paso a AUTH (esperando contraseña)
            ctx.state = "AUTH"
            ctx["state"] = "AUTH"
            return f"Usuario '{user}' guardado. Ahora dime tu contraseña."
        # No se pudo extraer: marco AUTH para que el siguiente input sea la contraseña o usuario
        ctx.state = "AUTH"
        ctx["state"] = "AUTH"
        return "Ok, dime tu usuario (ej: 'mi usuario es ana')."

    # 2) Tengo usuario, pero ¿tengo contraseña válida?
    if not auth_ok:
        # Intenta forma "mi contrasena es <token>"
        m_sent = re.search(PASS_SENTENCE_RE, text, re.I | re.X)
        token = None
        if m_sent:
            token = m_sent.group(1)
        else:
            # Intenta que el input completo sea la contraseña (solo token)
            m_tok = re.fullmatch(PASS_TOKEN_RE, text, re.I | re.X)
            if m_tok:
                token = m_tok.group(1)

        if token:
            # Marca autenticación OK (no guardamos el token por seguridad)
            ctx["auth_ok"] = True
            # Salta a CALIFICACIONES y muestra boleta
            ctx.state = "CALIFICACIONES"
            ctx["state"] = "CALIFICACIONES"
            return _render_calificaciones(ctx)

        # No pude extraer contraseña todavía
        return "Ahora dime tu contraseña (puedes escribir solo la contraseña o 'mi contrasena es <tu_clave>')."

    # 3) Ya autenticado: entrega calificaciones idempotente
    ctx.state = "CALIFICACIONES"
    ctx["state"] = "CALIFICACIONES"
    return _render_calificaciones(ctx)

# CLAVE: deja vacío para que el automáta NO pise el estado que setea el handler
NEXT_STATE = ""

# Permitido al inicio y mientras estamos autenticándonos
ALLOWED_STATES = {"START", "AUTH"}
