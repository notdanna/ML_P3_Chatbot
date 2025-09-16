# utils/modules/inscripcion.py
import re
import csv
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ------------------ Configuración ------------------

_GRUPOS_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "grupos.csv"

_LOGS_DIR = Path(__file__).resolve().parents[2] / "resources" / "logs"
_INSCRIPCIONES_LOG = _LOGS_DIR / "inscripciones.ndjson"

_GRUPOS_CACHE = None
_PERIODO_ACTUAL = "2025-1"

# Colores ANSI
_ANSI_RED = "\033[31m"
_ANSI_RESET = "\033[0m"
def _red(s: str) -> str:
    return f"{_ANSI_RED}{s}{_ANSI_RESET}"

# ------------------ Utilidades ------------------

def _load_grupos():
    """Carga el CSV de grupos a caché."""
    global _GRUPOS_CACHE
    if _GRUPOS_CACHE is not None:
        return _GRUPOS_CACHE

    rows = []
    try:
        with open(_GRUPOS_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                rows.append(row)
    except FileNotFoundError:
        rows = []

    _GRUPOS_CACHE = rows
    return _GRUPOS_CACHE


def _datos_disponibles():
    grupos = _load_grupos()
    if not grupos:
        return (False, f"No encuentro el archivo de grupos: '{_GRUPOS_CSV}'")
    return (True, None)


def _turno_label_from_code(code: str) -> str:
    c = (code or "").strip().lower()
    if c in ("m", "matutino"):
        return "Matutino"
    if c in ("v", "vespertino"):
        return "Vespertino"
    return ""


def _turno_code_from_label(lbl: str) -> str:
    l = (lbl or "").strip().lower()
    if l == "matutino":
        return "M"
    if l == "vespertino":
        return "V"
    return ""


def _int(v, default=0):
    try:
        return int(str(v).strip())
    except Exception:
        return default


def _disp(row) -> int:
    return _int(row.get("capacidad", 0)) - _int(row.get("inscritos", 0))


def _agrupar_por_grupo_y_turno(grupos_rows, turno_label: str):
    """
    Devuelve un dict { grupo_id: { 'turno':..., 'rows':[...], 'disp_min': int, 'disp_total': int } }
    filtrando por periodo actual y turno.
    """
    agg = {}
    for r in grupos_rows:
        if r.get("periodo_id", "") != _PERIODO_ACTUAL:
            continue
        if r.get("turno", "").lower() != turno_label.lower():
            continue
        gid = r.get("grupo_id", "")
        if not gid:
            continue
        disp = _disp(r)
        if gid not in agg:
            agg[gid] = {
                "turno": r.get("turno", ""),
                "rows": [r],
                "disp_min": disp,
                "disp_total": max(disp, 0),
            }
        else:
            agg[gid]["rows"].append(r)
            agg[gid]["disp_min"] = min(agg[gid]["disp_min"], disp)
            agg[gid]["disp_total"] += max(disp, 0)
    # Ordenamos por grupo_id
    return dict(sorted(agg.items(), key=lambda kv: kv[0]))


def _render_listado_turno(agg: dict) -> str:
    if not agg:
        return "No hay grupos disponibles para ese turno en el periodo actual."

    out = []
    out.append("Grupos disponibles:")
    out.append("-" * 22)
    for gid, data in agg.items():
        rows = data["rows"]
        materias_n = len(rows)
        # Tomamos un horario y salón de ejemplo (la primera fila)
        ejemplo = rows[0]
        horario = ejemplo.get("horario", "")
        modalidad = ejemplo.get("modalidad", "")
        salon = ejemplo.get("salon", "")
        disp_min = data["disp_min"]
        disp_txt = _red(str(disp_min)) if disp_min is not None else _red("?")

        out.append(f"- {gid} | {materias_n} materias | Horario ej.: {horario} ({modalidad}) | Salón ej.: {salon} | Cupo min: {disp_txt}")
    out.append("")
    out.append("Indica el grupo con:  grupo: 3CM2")
    return "\n".join(out)


def _append_inscripcion_log(entry: dict):
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_INSCRIPCIONES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _normaliza(s: str) -> str:
    return (s or "").strip().lower()


# ------------------ Disparadores / RE ------------------

INSCRIP_RE = r"\b(inscripcion|inscripciones|inscribirme|inscribir|alta\s+de\s+materias|inscribir\s+grupo)\b"

TURN0_RE = r"^\s*turno\s*[:=]?\s*(?P<t>(m|matutino|v|vespertino))\s*$"

GRUPO_RE = r"^\s*grupo\s*[:=]?\s*(?P<g>\d{1,2}C[MV]\d+)\s*$"


# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."

    # Validación de datos
    ok, err = _datos_disponibles()
    if not ok:
        return err

    grupos_rows = _load_grupos()

    # ---- Selección de turno ----
    m_turno = re.search(TURN0_RE, text, flags=re.I | re.X)
    if m_turno:
        t = m_turno.group("t").strip().lower()
        turno_label = _turno_label_from_code(t)  # "Matutino" | "Vespertino"
        if not turno_label:
            return "Turno no reconocido. Usa: turno: M   o   turno: V"

        ctx["insc_turno"] = "M" if turno_label == "Matutino" else "V"

        agg = _agrupar_por_grupo_y_turno(grupos_rows, turno_label)
        # Guardamos listado para el siguiente paso
        ctx["insc_listado"] = agg

        return (f"Muy bien, seleccionaste turno {turno_label}.\n"
                "Ahora dime qué grupo quieres meter, te muestro los disponibles:\n"
                f"{_render_listado_turno(agg)}")

    # ---- Selección de grupo ----
    m_grupo = re.search(GRUPO_RE, text, flags=re.I | re.X)
    if m_grupo:
        if not ctx.get("insc_turno"):
            return ("Primero selecciona turno.\n"
                    "Ejemplos:\n"
                    "  turno: M   (Matutino)\n"
                    "  turno: V   (Vespertino)")
        gid_req = m_grupo.group("g").strip().upper()
        turno_code = ctx["insc_turno"]
        turno_label = _turno_label_from_code(turno_code)

        # Recuperar listado guardado (o regenerar si no existe)
        agg = ctx.get("insc_listado")
        if not agg:
            agg = _agrupar_por_grupo_y_turno(grupos_rows, turno_label)

        data = agg.get(gid_req)
        if not data:
            # Recomendación similar
            similares = [g for g in agg.keys() if _normaliza(g).startswith(_normaliza(gid_req[:3]))]
            sug = f"Sugerencias: {', '.join(similares)}" if similares else "Verifica el listado."
            return (f"No identifiqué el grupo '{gid_req}' en turno {turno_label}.\n{sug}")

        # Cupo mínimo del grupo (se calcula a nivel materias)
        disp_min = data["disp_min"]
        hay_cupo = disp_min > 0

        # Armar payload de log
        now = datetime.now().isoformat(timespec="seconds")
        folio = f"INS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        materias = []
        for r in data["rows"]:
            materias.append({
                "materia_id": r.get("materia_id", ""),
                "nombre_materia": r.get("nombre_materia", ""),
                "profesor": r.get("profesor", ""),
                "horario": r.get("horario", ""),
                "modalidad": r.get("modalidad", ""),
                "salon": r.get("salon", ""),
                "capacidad": r.get("capacidad", ""),
                "inscritos": r.get("inscritos", ""),
                "disponibles": max(_disp(r), 0),
                "slots": r.get("slots", "")
            })

        entry = {
            "folio": folio,
            "ts": now,
            "periodo": _PERIODO_ACTUAL,
            "boleta": str(ctx.get("user", "")).strip(),
            "turno": {"code": turno_code, "label": turno_label},
            "grupo_id": gid_req,
            "resultado": "inscrito" if hay_cupo else "sin_cupo",
            "cupo_min_grupo": max(disp_min, 0),
            "materias": materias
        }

        try:
            _append_inscripcion_log(entry)
        except Exception as e:
            return f"Ocurrió un error al registrar la inscripción: {e}"

        if hay_cupo:
            return (f"De acuerdo, te inscribo en {gid_req} ({turno_label}).\n"
                    f"Cupo mínimo a nivel grupo: {_red(str(disp_min))}\n"
                    f"Se registró en: {str(_INSCRIPCIONES_LOG)}\n"
                    "¿Deseas ver el detalle de materias u otro grupo?")
        else:
            return (f"Lo intenté, pero {gid_req} ya se llenó (cupo mínimo: {_red(str(disp_min))}).\n"
                    f"Quedó registro en: {str(_INSCRIPCIONES_LOG)}\n"
                    "Elige otro grupo con:  grupo: <ID>")

    # ---- Inicio del flujo / ayuda ----
    if re.search(INSCRIP_RE, text, flags=re.I):
        return ("Proceso de inscripción:\n"
                "1) Elige turno (M=mañana, V=tarde):\n"
                "     turno: M    o    turno: V\n"
                "2) Elige grupo (por ejemplo):\n"
                "     grupo: 3CM2\n")

    # Si no matchea nada, mensaje guía
    return ("Para inscribirte, primero indica el turno:\n"
            "  turno: M   (Matutino)\n"
            "  turno: V   (Vespertino)\n"
            "Luego indica el grupo:\n"
            "  grupo: 3CM2")


# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
