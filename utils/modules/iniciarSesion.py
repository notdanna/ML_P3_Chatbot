# utils/modules/iniciarSesion.py
import re
import csv
from pathlib import Path

# ---- Configuración de datos -----------------------------------------------

# Ruta absoluta al CSV: <PROJECT_ROOT>/resources/data/alumnos.csv
_CSV_PATH = Path(__file__).resolve().parents[2] / "resources" / "data" / "alumnos.csv"

# Caché en memoria de los alumnos (boleta -> dict(row))
_ALUMNOS_CACHE = None


def _load_alumnos():
    """Carga el CSV de alumnos una sola vez y lo deja en caché.
    Estructura esperada de columnas:
      boleta,nombre,correo,plan,estatus,contrasena
    """
    global _ALUMNOS_CACHE
    if _ALUMNOS_CACHE is not None:
        return _ALUMNOS_CACHE

    alumnos = {}
    try:
        # utf-8-sig para soportar BOM si el archivo lo tiene
        with open(_CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            # Normalizamos llaves por si el CSV trae mayúsculas/minúsculas
            # y quitamos espacios
            for raw in reader:
                row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                boleta = row.get("boleta", "")
                if boleta:
                    alumnos[boleta] = row
    except FileNotFoundError:
        alumnos = {}

    _ALUMNOS_CACHE = alumnos
    return _ALUMNOS_CACHE


def _alumnos_disponibles():
    """Devuelve (ok: bool, msg_error: str | None)."""
    alumnos = _load_alumnos()
    if not alumnos:
        return (False,
                f"No encuentro el archivo de alumnos o está vacío: '{_CSV_PATH}'. "
                "Verifica la ruta y el contenido (boleta,nombre,correo,plan,estatus,contrasena).")
    return (True, None)


# ---- Expresiones regulares -------------------------------------------------

# Disparadores para iniciar sesión
LOGIN_RE = r"""
\b(
    iniciar\s*sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign(?:\s*in)? | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes | hola
)\b
"""

# Usuario: acepta boletas de 10 dígitos (p.ej. 2023630000), con o sin "mi usuario es".
# La validación real se hace contra el CSV.
USER_RE = r"\b(?:mi\s+usuario\s+es\s+)?(\d{10})\b"

# Contraseña: "mi contrasena es <token>" o solo el token en toda la línea
PASS_SENTENCE_RE = r"\bmi\s+contrasena\s+es\s+([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\b"
PASS_TOKEN_RE    = r"^\s*([A-Za-z0-9@#$%^&*().,;:!_\-]{4,})\s*$"


# ---- Handler ---------------------------------------------------------------

def handle(ctx, text):
    """
    Flujo:
      1) Pedir/guardar boleta si no hay usuario en contexto.
         - Verificar que la boleta exista en el CSV.
      2) Pedir/validar contraseña si aún no está autenticado.
         - Comparar contra 'contrasena' del CSV para esa boleta.
      3) Si ya autenticado, mostrar opciones.
    """
    user = ctx.get("user")
    auth_ok = ctx.get("auth_ok", False)

    # Validamos disponibilidad del CSV antes de cualquier cosa:
    ok_data, err = _alumnos_disponibles()
    if not ok_data:
        # Mantenemos el flujo en AUTH para que el bot no quede "muerto"
        ctx.state = ctx["state"] = "AUTH"
        return err

    alumnos = _load_alumnos()

    # 1) Usuario (boleta)
    if not user:
        m_user = re.search(USER_RE, text, re.I | re.X)
        if m_user:
            boleta = m_user.group(1)
            if boleta not in alumnos:
                ctx.state = ctx["state"] = "AUTH"
                return (f"La boleta {boleta} no aparece en el sistema. "
                        "Verifícala o ingresa otra (ej: 2023630000).")

            # Guardamos usuario y datos del alumno
            ctx["user"] = boleta
            ctx["alumno"] = alumnos[boleta]
            ctx.state = ctx["state"] = "AUTH"
            return f"Usuario '{boleta}' encontrado. Ahora dime tu contraseña."

        ctx.state = ctx["state"] = "AUTH"
        return "Hola, dime tu usuario (boleta de 10 dígitos, ej: 2023630000)."

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
            boleta = ctx["user"]
            alumno = alumnos.get(boleta, {})
            pwd_csv = (alumno.get("contrasena") or "").strip()
            if token == pwd_csv:
                ctx["auth_ok"] = True
                ctx.state = ctx["state"] = "AUTH_OK"
                return ("¡Ya estás adentro! Pide lo que necesites: "
                        "'ver calificaciones', 'info academica', 'info personal', "
                        "'materias', 'tramites', 'inscripcion' u 'opciones'.")
            else:
                ctx.state = ctx["state"] = "AUTH"
                return "Contraseña incorrecta. Inténtalo de nuevo."

        return ("Ahora dime tu contraseña (puedes escribir solo la contraseña o "
                "'mi contrasena es <tu_clave>').")

    # 3) Ya autenticado
    ctx.state = ctx["state"] = "AUTH_OK"
    return ("Ya estás adentro. Opciones: 'ver calificaciones', 'info academica', "
            "'info personal', 'materias', 'tramites', 'inscripcion' u 'opciones'.")

# No pisamos el estado desde el autómata; lo controla el handler
NEXT_STATE = ""
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK"}
