# utils/modules/inscripcion.py
import re
import csv
import json
from datetime import datetime
from pathlib import Path

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
    """Carga el CSV de grupos a caché (keys en minúsculas)."""
    global _GRUPOS_CACHE
    if _GRUPOS_CACHE is not None:
        return _GRUPOS_CACHE

    rows = []
    try:
        with open(_GRUPOS_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
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
    Dict { grupo_id: { 'turno':..., 'rows':[...], 'disp_min': int, 'disp_total': int } }
    Filtra por periodo actual y turno; ordenado por grupo_id.
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
    return dict(sorted(agg.items(), key=lambda kv: kv[0]))


def _render_listado_turno(agg: dict) -> str:
    if not agg:
        return "No hay grupos disponibles para ese turno en el periodo actual."

    out = []
    out.append("Grupos disponibles:")
    out.append("-" * 22)
    for gid, data in agg.items():
        rows = data["rows"]
        ejemplo = rows[0]
        horario = ejemplo.get("horario", "")
        modalidad = ejemplo.get("modalidad", "")
        salon = ejemplo.get("salon", "")
        disp_min = data["disp_min"]
        disp_txt = _red(str(disp_min)) if disp_min is not None else _red("?")
        out.append(f"- {gid} | {len(rows)} materias | Horario ej.: {horario} ({modalidad}) | Salón ej.: {salon} | Cupo min: {disp_txt}")
    out.append("")
    out.append("Indica el grupo con:  grupo: 3CV2")
    out.append("Para cambiar de turno:  turno: M   o   turno: V")
    out.append("Reiniciar el flujo:  reiniciar")
    return "\n".join(out)


def _append_inscripcion_log(entry: dict):
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_INSCRIPCIONES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _normaliza(s: str) -> str:
    return (s or "").strip().lower()


def _buscar_grupo_en_todos(grupos_rows, gid: str):
    gid_up = (gid or "").strip().upper()
    res = [r for r in grupos_rows if (r.get("grupo_id", "").strip().upper() == gid_up and r.get("periodo_id") == _PERIODO_ACTUAL)]
    return res  # puede estar en M o V (distintas materias/rows)


def _log_evento(ctx, turno_label, gid_req, resultado, detalle=None, materias_rows=None):
    now = datetime.now().isoformat(timespec="seconds")
    folio = f"INS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    entry = {
        "folio": folio,
        "ts": now,
        "periodo": _PERIODO_ACTUAL,
        "boleta": str(ctx.get("user", "")).strip(),
        "turno": {"code": ctx.get("insc_turno", ""), "label": turno_label},
        "grupo_id": gid_req,
        "resultado": resultado
    }
    if detalle is not None:
        entry["detalle"] = detalle
    if materias_rows:
        entry["materias"] = [{
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
        } for r in materias_rows]
    try:
        _append_inscripcion_log(entry)
    except Exception:
        pass
    return folio

# ------------------ Disparadores / RE ------------------

INSCRIP_RE = r"\b(inscripcion|inscripciones|inscribirme|inscribir|alta\s+de\s+materias|inscribir\s+grupo)\b"
TURN0_RE   = r"^\s*turno\s*[:=]?\s*(?P<t>(m|matutino|v|vespertino))\s*$"
GRUPO_RE   = r"^\s*grupo\s*[:=]?\s*(?P<g>\d{1,2}C[MV]\d+)\s*$"

# **NUEVO**: dudas genéricas mientras estás en el flujo
UNCERTAIN_RE = r"^\s*(no\s*s[eé]|no\s*se\s*que\s*elegir|no\s*estoy\s*seguro|ayuda|opciones|men[úu]|menu|ver\s+grupos|listar|lista)\s*$"
REINICIAR_RE = r"^\s*(reiniciar|cancelar(\s+inscripci[oó]n)?|empezar\s+de\s+nuevo)\s*$"
CAMBIAR_TURNO_RE = r"^\s*(cambiar\s+turno|otro\s+turno)\s*$"

# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."

    ok, err = _datos_disponibles()
    if not ok:
        return err

    grupos_rows = _load_grupos()

    # ---- Reiniciar flujo ----
    if re.search(REINICIAR_RE, text, flags=re.I | re.X):
        ctx.pop("insc_turno", None)
        ctx.pop("insc_listado", None)
        return ("Flujo de inscripción reiniciado.\n"
                "1) Elige turno (M=mañana, V=tarde):\n"
                "     turno: M    o    turno: V\n"
                "2) Elige grupo (por ejemplo):\n"
                "     grupo: 3CM2")

    # ---- Cambiar turno (atajo) ----
    if re.search(CAMBIAR_TURNO_RE, text, flags=re.I | re.X):
        return ("Indica el nuevo turno:\n"
                "  turno: M   (Matutino)\n"
                "  turno: V   (Vespertino)")

    # ---- Selección de turno ----
    m_turno = re.search(TURN0_RE, text, flags=re.I | re.X)
    if m_turno:
        t = m_turno.group("t").strip().lower()
        turno_label = _turno_label_from_code(t)
        if not turno_label:
            return "Turno no reconocido. Usa: turno: M   o   turno: V"

        ctx["insc_turno"] = "M" if turno_label == "Matutino" else "V"
        agg = _agrupar_por_grupo_y_turno(grupos_rows, turno_label)
        ctx["insc_listado"] = agg

        return (f"Muy bien, seleccionaste turno {turno_label}.\n"
                "Ahora dime qué grupo quieres meter, te muestro los disponibles:\n"
                f"{_render_listado_turno(agg)}")

    # ---- Listar / ayuda contextual ----
    if re.search(UNCERTAIN_RE, text, flags=re.I | re.X):
        turno_code = ctx.get("insc_turno")
        if not turno_code:
            return ("Para inscribirte, primero indica el turno:\n"
                    "  turno: M   (Matutino)\n"
                    "  turno: V   (Vespertino)")
        turno_label = _turno_label_from_code(turno_code)
        agg = ctx.get("insc_listado") or _agrupar_por_grupo_y_turno(grupos_rows, turno_label)
        ctx["insc_listado"] = agg
        return (f"Sigues en turno {turno_label}. Aquí están los grupos:\n"
                f"{_render_listado_turno(agg)}")

    # ---- Selección de grupo ----
    m_grupo = re.search(GRUPO_RE, text, flags=re.I | re.X)
    if m_grupo:
        if not ctx.get("insc_turno"):
            return ("Primero selecciona turno.\n"
                    "  turno: M   (Matutino)\n"
                    "  turno: V   (Vespertino)")
        gid_req = m_grupo.group("g").strip().upper()
        turno_code = ctx["insc_turno"]
        turno_label = _turno_label_from_code(turno_code)

        agg = ctx.get("insc_listado") or _agrupar_por_grupo_y_turno(grupos_rows, turno_label)
        ctx["insc_listado"] = agg

        data = agg.get(gid_req)
        if not data:
            # ¿Existe ese grupo en otro turno?
            en_todos = _buscar_grupo_en_todos(grupos_rows, gid_req)
            if en_todos:
                turno_real = (en_todos[0].get("turno") or "").strip()
                folio = _log_evento(ctx, turno_label, gid_req, "turno_mismatch",
                                    detalle=f"Grupo {gid_req} pertenece a turno {turno_real}")
                # Sugerencias del turno actual
                suger = ", ".join(list(agg.keys())[:3]) if agg else "sin opciones"
                return (f"El grupo '{gid_req}' pertenece al turno {turno_real}, pero ahora estás en {turno_label}.\n"
                        "¿Quieres cambiar de turno o elegir uno de estos?\n"
                        f"- Cambiar turno:  turno: {'M' if turno_real.lower().startswith('m') else 'V'}\n"
                        f"- Sugerencias {turno_label}: {suger}\n"
                        f"(Se registró el intento como {folio})")
            else:
                # Sugerencias por prefijo
                pref = gid_req[:3]
                similares = [g for g in agg.keys() if _normaliza(g).startswith(_normaliza(pref))]
                sug = f"Sugerencias: {', '.join(similares)}" if similares else "Verifica el listado con 'ver grupos'."
                folio = _log_evento(ctx, turno_label, gid_req, "grupo_no_en_turno")
                return (f"No identifiqué el grupo '{gid_req}' en turno {turno_label}.\n"
                        f"{sug}\n"
                        f"(Intento registrado: {folio})")

        # Cupo a nivel grupo (mínimo entre materias)
        disp_min = data["disp_min"]
        hay_cupo = disp_min > 0

        # Construimos materias para log
        materias_rows = data["rows"]
        resultado = "inscrito" if hay_cupo else "sin_cupo"
        folio = _log_evento(ctx, turno_label, gid_req, resultado, materias_rows=materias_rows)

        if hay_cupo:
            return (f"De acuerdo, te inscribo en {gid_req} ({turno_label}).\n"
                    f"Cupo mínimo a nivel grupo: {_red(str(disp_min))}\n"
                    f"Se registró en: {str(_INSCRIPCIONES_LOG)}\n"
                    "¿Deseas ver el detalle de materias u otro grupo?")
        else:
            # Ofrecer alternativas con mayor cupo
            alternativas = sorted(
                [(g, d["disp_min"]) for g, d in agg.items() if d["disp_min"] > 0 and g != gid_req],
                key=lambda x: -x[1]
            )[:3]
            alt_txt = ", ".join([f"{g} (cupo {_red(str(dm))})" for g, dm in alternativas]) if alternativas else "No encontré alternativas con cupo en este turno."
            return (f"Lo intenté, pero {gid_req} ya se llenó (cupo mínimo: {_red(str(disp_min))}).\n"
                    f"Sugerencias: {alt_txt}\n"
                    f"Quedó registro en: {str(_INSCRIPCIONES_LOG)}\n"
                    "Elige otro grupo con:  grupo: <ID>   o cambia de turno:  turno: M/V")

    # ---- Inicio del flujo / ayuda general ----
    if re.search(INSCRIP_RE, text, flags=re.I):
        return ("Proceso de inscripción:\n"
                "1) Elige turno (M=mañana, V=tarde):\n"
                "     turno: M    o    turno: V\n"
                "2) Elige grupo (por ejemplo):\n"
                "     grupo: 3CM2\n"
                "Tip: si te atoras, escribe 'opciones' o 'ver grupos'.")

    # ---- Si no matchea nada y hay contexto, devolvemos ayuda contextual ----
    if ctx.get("insc_turno"):
        turno_label = _turno_label_from_code(ctx["insc_turno"])
        agg = ctx.get("insc_listado") or _agrupar_por_grupo_y_turno(grupos_rows, turno_label)
        ctx["insc_listado"] = agg
        return (f"No entendí, pero sigues en turno {turno_label}.\n"
                f"{_render_listado_turno(agg)}")

    # Mensaje guía por defecto
    return ("Para inscribirte, primero indica el turno:\n"
            "  turno: M   (Matutino)\n"
            "  turno: V   (Vespertino)\n"
            "Luego indica el grupo:\n"
            "  grupo: 3CV2   (o escribe 'inscripcion' para ver los pasos)")

# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
