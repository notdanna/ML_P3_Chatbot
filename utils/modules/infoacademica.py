# utils/modules/infoacademica.py
from __future__ import annotations
import re
import csv
from pathlib import Path

# ================== Configuración de datos ==================

# Ruta absoluta al CSV: <PROJECT_ROOT>/resources/data/infoAlumnos.csv
# (Se arma de forma relativa al proyecto para no depender del cwd)
_CSV_PATH = Path(__file__).resolve().parents[2] / "resources" / "data" / "infoAlumnos.csv"

# Caché simple con invalidación por mtime
_INFO_CACHE = None           # tipo: tuple[list[dict], bool]
_CACHED_MTIME = None         # tipo: float | None

# Normalización de boleta (quitar no-dígitos)
_DIGITS_RE = re.compile(r"\D+")

def _norm_boleta(s: str) -> str:
    return _DIGITS_RE.sub("", (s or "").strip())


# ================== Carga de CSV ==================

def _load_infoalumnos():
    """
    Carga el CSV infoAlumnos en memoria con caché por mtime.
    Devuelve (rows:list[dict], has_boleta:bool)
    """
    global _INFO_CACHE, _CACHED_MTIME
    try:
        mtime = _CSV_PATH.stat().st_mtime
    except FileNotFoundError:
        _INFO_CACHE = ([], False)
        _CACHED_MTIME = None
        return _INFO_CACHE

    if _INFO_CACHE is not None and _CACHED_MTIME == mtime:
        return _INFO_CACHE

    rows = []
    has_boleta = False
    with open(_CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            # normalizamos llaves en minúsculas sin espacios
            row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
            rows.append(row)
        if rows:
            # basta con inspeccionar la primera fila para saber si existe 'boleta'
            has_boleta = "boleta" in rows[0]

    _INFO_CACHE = (rows, has_boleta)
    _CACHED_MTIME = mtime
    return _INFO_CACHE


def _info_disponible():
    """Verifica que el archivo exista y tenga contenido."""
    rows, _ = _load_infoalumnos()
    if not rows:
        return (False,
                f"No encuentro información de alumnos o el archivo está vacío: '{_CSV_PATH}'. "
                "Asegúrate de crearlo con encabezados como: "
                "'boleta,nombre,plantel,sexo,fechanacimiento,nacionalidad,entidadnacimiento,direccion,telefono,correo'.")
    return (True, None)


# ================== Utilidades de acceso ==================

# alias de encabezados tolerantes (por si vienen con pequeñas variaciones)
ALIASES = {
    "boleta": {"boleta", "id", "matricula"},
    "nombre": {"nombre", "alumno", "estudiante"},
    "plantel": {"plantel", "escuela", "campus"},
    "sexo": {"sexo", "genero", "género"},
    "fechanacimiento": {"fechanacimiento", "fecha_nacimiento", "nacimiento", "dob"},
    "nacionalidad": {"nacionalidad", "pais", "país"},
    "entidadnacimiento": {"entidadnacimiento", "lugar_nacimiento", "estado_nacimiento"},
    "direccion": {"direccion", "dirección", "domicilio"},
    "telefono": {"telefono", "teléfono", "phone"},
    "correo": {"correo", "email", "mail"},
}

def _get(row: dict, key: str, default: str = "") -> str:
    keys = ALIASES.get(key, {key})
    for k in keys:
        if k in row:
            return row.get(k, default)
    return default


def _render_info(rows: list[dict], limit: int | None = None) -> str:
    out = []
    for idx, r in enumerate(rows):
        boleta = _get(r, "boleta")
        nombre = _get(r, "nombre")
        plantel = _get(r, "plantel")
        sexo = _get(r, "sexo")
        fnac = _get(r, "fechanacimiento")
        nac = _get(r, "nacionalidad")
        ent = _get(r, "entidadnacimiento")
        dir_ = _get(r, "direccion")
        tel = _get(r, "telefono")
        mail = _get(r, "correo")

        # Construcción legible
        lineas = []
        if nombre or boleta:
            cab = (f"{nombre}" if nombre else "Alumno") + (f" — Boleta {boleta}" if boleta else "")
            lineas.append(f"- {cab}")
        if plantel:
            lineas.append(f"  Plantel: {plantel}")
        if sexo:
            lineas.append(f"  Sexo: {sexo}")
        if fnac:
            lineas.append(f"  Fecha de nacimiento: {fnac}")
        if nac or ent:
            linea = "  Nacionalidad/Entidad: "
            if nac and ent:
                linea += f"{nac}, {ent}"
            else:
                linea += f"{nac or ent}"
            lineas.append(linea)
        if dir_:
            lineas.append(f"  Dirección: {dir_}")
        if tel:
            lineas.append(f"  Teléfono: {tel}")
        if mail:
            lineas.append(f"  Correo: {mail}")

        out.append("\n".join(lineas))

        if limit is not None and (idx + 1) >= limit:
            break

    return "\n\n".join(out)


# ================== Disparador / RE ==================

INFOACAD_RE = r"""
\b(
    info(\s*academica)? | kardex | historial\s*academico |
    informacion\s*academica | datos\s*academicos
)\b
"""


# ================== Handler ==================

def handle(ctx, text):
    # Debe estar logueado
    if not ctx.get("user"):
        return "Primero inicia sesión."
    if not ctx.get("auth_ok"):
        return "Dime tu contraseña primero."

    ok, err = _info_disponible()
    if not ok:
        return err

    rows, has_boleta = _load_infoalumnos()
    user_boleta = _norm_boleta(ctx.get("user", ""))

    if has_boleta:
        # Filtrar por boleta del usuario (normalizada)
        mine = [r for r in rows if _norm_boleta(_get(r, "boleta")) == user_boleta]
        if not mine:
            return (f"No encontré información en '{_CSV_PATH.name}' para tu boleta {user_boleta}. "
                    "Verifica con servicios escolares si ya fue capturada. "
                    "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")
        listado = _render_info(mine)
        return (f"Información académica básica ({user_boleta}):\n{listado}\n\n"
                "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")
    else:
        # Modo compatible: sin 'boleta' → mostrar un resumen general (limitado)
        aviso = ("Aviso: el archivo 'infoAlumnos.csv' no tiene columna 'boleta'. "
                 "Te muestro un resumen general. Para personalizar por alumno, "
                 "añade la columna 'boleta' y una fila por estudiante.")
        listado = _render_info(rows, limit=20)
        extra = f"\n\n… y {max(0, len(rows)-20)} más." if len(rows) > 20 else ""
        return (f"{aviso}\n\n{listado}{extra}\n\n"
                "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")

# Mantener subflujo y compatibilidad con el autómata
NEXT_STATE = "INFO_ACADEMICA"
ALLOWED_STATES = {"AUTH_OK", "INFO_ACADEMICA", "CALIFICACIONES"}
