# utils/modules/calificaciones.py
import re
import csv
from pathlib import Path

# ------------------ Configuración de datos ------------------

# Ruta absoluta al CSV: <PROJECT_ROOT>/resources/data/calificaciones.csv
_CSV_PATH = Path(__file__).resolve().parents[2] / "resources" / "data" / "calificaciones.csv"

# Caché simple en memoria
_CALIF_CACHE = None


def _load_califs():
    """Carga el CSV de calificaciones y lo deja en caché.
    Devuelve (rows:list[dict], has_boleta:bool)
    """
    global _CALIF_CACHE
    if _CALIF_CACHE is not None:
        return _CALIF_CACHE

    rows = []
    has_boleta = False
    try:
        with open(_CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                rows.append(row)
            # Detectamos si el CSV trae columna 'boleta'
            if rows:
                has_boleta = "boleta" in rows[0]
    except FileNotFoundError:
        rows = []
        has_boleta = False

    _CALIF_CACHE = (rows, has_boleta)
    return _CALIF_CACHE


def _califs_disponibles():
    """Verifica que existan calificaciones cargables."""
    rows, _ = _load_califs()
    if not rows:
        return (False,
                f"No encuentro calificaciones o el archivo está vacío: '{_CSV_PATH}'. "
                "Asegúrate de crearlo con encabezados "
                "'boleta,materia,grupo_id,periodo_id,parcial1,parcial2,final,resultado'.")
    return (True, None)


def _render_califs(rows, limit=None):
    """Convierte filas de calificaciones a un texto legible."""
    out = []
    count = 0
    for r in rows:
        materia   = r.get("materia", "Materia")
        grupo_id  = r.get("grupo_id", "")
        periodo   = r.get("periodo_id", "")
        p1        = r.get("parcial1", "")
        p2        = r.get("parcial2", "")
        fin       = r.get("final", "")
        res       = r.get("resultado", "")

        linea = f"- {materia}"
        extras = []
        if grupo_id:
            extras.append(f"Grupo {grupo_id}")
        if periodo:
            extras.append(f"Periodo {periodo}")
        if extras:
            linea += " (" + ", ".join(extras) + ")"
        notas = []
        if p1 != "":
            notas.append(f"P1 {p1}")
        if p2 != "":
            notas.append(f"P2 {p2}")
        if fin != "":
            notas.append(f"Final {fin}")
        if notas:
            linea += f": " + ", ".join(notas)
        if res:
            linea += f" — {res}"
        out.append(linea)

        count += 1
        if limit is not None and count >= limit:
            break

    return "\n".join(out)


# ------------------ Disparador / RE ------------------

CALIF_RE = r"\b(calificacion(?:es)?|ver\s+calificacion(?:es)?)\b"


# ------------------ Handler ------------------

def handle(ctx, text):
    # Debe estar logueado
    if not ctx.get("user"):
        return "Primero inicia sesión."
    if not ctx.get("auth_ok"):
        return "Dime tu contraseña primero."

    ok, err = _califs_disponibles()
    if not ok:
        return err

    rows, has_boleta = _load_califs()
    boleta = str(ctx.get("user", "")).strip()

    if has_boleta:
        # Filtrar por la boleta del usuario
        mine = [r for r in rows if r.get("boleta", "").strip() == boleta]
        if not mine:
            msg = (f"No encontré calificaciones registradas para tu boleta {boleta}. "
                   "Verifica con servicios escolares si ya fueron capturadas.")
            return msg + " ¿Quieres 'info academica', 'materias', 'tramites' o 'inscripcion'?"
        listado = _render_califs(mine)
        return (f"Tus calificaciones ({boleta}):\n{listado}\n\n"
                "¿Quieres 'info academica', 'materias', 'tramites' o 'inscripcion'?")
    else:

        listado = _render_califs(rows, limit=20)
        if len(rows) > 20:
            listado += f"\n… y {len(rows)-20} más."
        return (f"\n\n{listado}\n\n"
                "¿Quieres 'info academica', 'materias', 'tramites' o 'inscripcion'?")

# Sugerimos mantener este estado para subflujo de calificaciones
NEXT_STATE = "AUTH_OK"  # Mantener el estado de autenticado
ALLOWED_STATES = {"AUTH_OK"}  # Solo necesita estar autenticado
