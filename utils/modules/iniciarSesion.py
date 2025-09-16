# utils/modules/iniciarSesion.py
import re

LOGIN_RE = r"""
\b(
    iniciar\s*sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign(?:\s*in)? | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes | hola
)\b
"""

# Usuario (permite letras/numeros . _ - y espacios internos)
USER_RE = r"\bmi\s+usuario\s+es\s+([A-Za-z0-9._-]+(?:\s+[A-Za-z0-9._-]+)*)"

# Contrasena: "mi contrasena es <token>" o solo el token en toda la linea
PASS_SENTENCE_RE = r"\bmi\s+contrasena\s+es\s+([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\b"
PASS_TOKEN_RE    = r"^\s*([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\s*$"

def handle(ctx, text):
    user = ctx.get("user")
    auth_ok = ctx.get("auth_ok", False)

    # 1) Usuario
    if not user:
        m_user = re.search(USER_RE, text, re.I | re.X)
        if m_user:
            ctx["user"] = m_user.group(1)
            ctx.state = ctx["state"] = "AUTH"
            return f"Usuario '{ctx['user']}' guardado. Ahora dime tu contraseña."
        ctx.state = ctx["state"] = "AUTH"
        return "Ok, dime tu usuario (ej: 'mi usuario es Miguel123')."

    # 2) Contrasena
    if not auth_ok:
        token = None
        m = re.search(PASS_SENTENCE_RE, text, re.I | re.X)
        if m:
            token = m.group(1)
        else:
            m2 = re.fullmatch(PASS_TOKEN_RE, text, re.I | re.X)
            if m2:
                token = m2.group(1)

        if token:
            ctx["auth_ok"] = True
            ctx.state = ctx["state"] = "AUTH_OK"
            return ("¡Ya estás adentro! Pide lo que necesites: "
                    "'ver calificaciones', 'info academica', 'info personal', "
                    "'materias', 'tramites', 'inscripcion' u 'opciones'.")
        return ("Ahora dime tu contraseña (puedes escribir solo la contraseña o "
                "'mi contrasena es <tu_clave>').")

    # 3) Ya autenticado
    ctx.state = ctx["state"] = "AUTH_OK"
    return ("Ya estás adentro. Opciones: 'ver calificaciones', 'info academica', "
            "'info personal', 'materias', 'tramites', 'inscripcion' u 'opciones'.")

# No pisamos el estado desde el automata; lo controla el handler
NEXT_STATE = ""
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK"}
