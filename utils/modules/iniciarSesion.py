# utils/modules/iniciarSesion.py
import re

# Disparadores para iniciar sesión
LOGIN_RE = r"""
\b(
    iniciar\s*sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign(?:\s*in)? | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes | hola
)\b
"""

# Usuario: acepta SOLO IDs del tipo 202363XXXX (cuatro dígitos al final).
# Soporta con o sin la frase "mi usuario es ".
USER_RE = r"\b(?:mi\s+usuario\s+es\s+)?(202363\d{4})\b"

# Contraseña: "mi contrasena es <token>" o solo el token en toda la línea
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
        return "Ok, dime tu usuario (ej: 2023631234)."

    # 2) Contraseña
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
            return ("¡Ya estás adentro1 Pide lo que necesites: "
                    "'ver calificaciones', 'info academica', 'info personal', "
                    "'materias', 'tramites', 'inscripcion' u 'opciones'.")
        return ("Ahora dime tu contraseña (puedes escribir solo la contraseña o "
                "'mi contrasena es <tu_clave>').")

    # 3) Ya autenticado
    ctx.state = ctx["state"] = "AUTH_OK"
    return ("Hmm, no estoy seguro de poder ayudarte con eso. Aqui te dejo una lista de mis capacidades: "
    "'calificaciones', 'kerdex', 'información personal', " "'informacion academica', 'horarios', 'materias', 'tramites', 'inscripcion'.")

# No pisamos el estado desde el autómata; lo controla el handler
NEXT_STATE = ""
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK", "END"}
