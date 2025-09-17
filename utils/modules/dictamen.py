# utils/modules/dictamen.py
import re
import csv
import json
from datetime import datetime
from pathlib import Path

# ------------------ Configuración de datos ------------------


# Rutas absolutas
_KARDEX_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "kardex.csv"

# Logs (NDJSON)
_LOGS_DIR = Path(__file__).resolve().parents[2] / "resources" / "logs"
_DICTAMEN_LOG = _LOGS_DIR / "dictamen.ndjson"

# Caché simple en memoria
_KARDEX_CACHE = None

# Periodo actual (ajústalo si lo manejas en otro lado)
_PERIODO_ACTUAL = "2025-1"


# ------------------ Utilidades de carga ------------------

def _load_kardex():
    """Carga el CSV del kardex y lo deja en caché. Devuelve (rows, has_boleta)."""
    global _KARDEX_CACHE
    if _KARDEX_CACHE is not None:
        return _KARDEX_CACHE

    rows = []
    has_boleta = False
    try:
        with open(_KARDEX_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
                rows.append(row)
            if rows:
                has_boleta = "boleta" in rows[0]
    except FileNotFoundError:
        rows = []
        has_boleta = False

    _KARDEX_CACHE = (rows, has_boleta)
    return _KARDEX_CACHE


def _datos_disponibles():
    kardex, _ = _load_kardex()
    if not kardex:
        return (False, f"No encuentro el archivo de kardex: '{_KARDEX_CSV}'")
    return (True, None)


# ------------------ Lógica de dictamen ------------------

def _calcular_diferencia_semestres(semestre_reprobado, semestre_actual=_PERIODO_ACTUAL):
    """Calcula la diferencia en semestres entre cuando se reprobó y el semestre actual.
    Formato esperado: 'YYYY-1' o 'YYYY-2'."""
    try:
        a_r, p_r = semestre_reprobado.split("-")
        a_r = int(a_r); p_r = int(p_r)

        a_a, p_a = semestre_actual.split("-")
        a_a = int(a_a); p_a = int(p_a)

        return (a_a * 2 + p_a) - (a_r * 2 + p_r)
    except Exception:
        return 0  # Si no se puede parsear, consideramos que es reciente


def _encontrar_materias_dictamen(kardex_usuario):
    """Devuelve lista de materias reprobadas que requieren dictamen (>3 semestres)."""
    res = []
    for r in kardex_usuario:
        calif_s = r.get("calificacion", "").strip()
        if not calif_s:
            continue
        try:
            calif = float(calif_s)
        except ValueError:
            continue
        if calif >= 6:
            continue

        semestre = r.get("semestre", "")
        semestres_transcurridos = _calcular_diferencia_semestres(semestre)
        if semestres_transcurridos > 3:
            info = r.copy()
            info["semestres_transcurridos"] = semestres_transcurridos
            res.append(info)
    return res


def _append_dictamen_log(entry: dict):
    """Agrega una línea NDJSON al archivo de dictamen."""
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_DICTAMEN_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _normaliza(s: str) -> str:
    return (s or "").strip().lower()


# ------------------ Disparadores / RE ------------------
# 1) Invocar módulo / ver materias con dictamen
DICTAMEN_RE = r"""
\b(
    dictamen
  | carta\s+de\s+dictamen
  | solicitar\s+dictamen
  | autorizaci(?:on|ón)\s+(?:para\s+)?ets
  | carta\s+de\s+motivos
  | motivos\s+para\s+dictamen
)\b
"""

# 2) Seleccionar materia por número o por nombre:
#    "dictamen 2"  o  "dictamen Sistemas Operativos"
DICTAMEN_SELECT_RE = r"""
^\s*dictamen\s+(
    (?P<num>\d{1,2})        # opción numérica
  | (?P<name>.+)            # o el nombre textual
)\s*$
"""

# 3) Enviar carta de motivos (recomendamos este prefijo para poder rutear)
#    "carta: <texto de la carta>"
DICTAMEN_CARTA_RE = r"""
^\s*carta\s*:\s*(?P<carta>.+)$
"""


# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."

    # Asegurar datos
    ok, err = _datos_disponibles()
    if not ok:
        return err

    kardex, has_boleta = _load_kardex()
    if not has_boleta:
        return ("El archivo de kardex no tiene columna 'boleta'. "
                "No puedo identificar tus materias específicas.")

    boleta = str(ctx.get("user", "")).strip()
    if not boleta:
        return "Primero necesito tu boleta (inicia sesión)."

    # Filtrar kardex del usuario
    kuser = [r for r in kardex if _normaliza(r.get("boleta")) == _normaliza(boleta)]
    if not kuser:
        return (f"No encontré tu historial académico (boleta {boleta}). "
                "Verifica con servicios escolares.")

    # 3) Si el usuario envió una carta y ya hay una materia seleccionada:
    m_carta = re.search(DICTAMEN_CARTA_RE, text, flags=re.I | re.X)
    if m_carta:
        pending = ctx.get("dictamen_selected")
        if not pending:
            return ("Primero selecciona la materia de dictamen.\n"
                    "Ejemplos: 'dictamen 2' o 'dictamen Nombre de la Materia'.")
        carta = m_carta.group("carta").strip()
        if not carta:
            return "Tu carta está vacía. Intenta de nuevo con: 'carta: <tu texto>'."

        # Construimos entrada
        now = datetime.now().isoformat(timespec="seconds")
        folio = f"DIC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entrada = {
            "folio": folio,
            "ts": now,
            "periodo_actual": _PERIODO_ACTUAL,
            "boleta": boleta,
            "materia": pending.get("materia", "desconocida"),
            "semestre_cursado": pending.get("semestre", ""),
            "calificacion": pending.get("calificacion", ""),
            "grupo_original": pending.get("grupo", ""),
            "profesor_original": pending.get("profesor", ""),
            "semestres_transcurridos": pending.get("semestres_transcurridos", 0),
            "tipo": "solicitud_dictamen",
            "carta_motivos": carta,
            "estatus": "pendiente"
        }

        try:
            _append_dictamen_log(entrada)
        except Exception as e:
            return f"Ocurrió un error al guardar tu carta: {e}"

        # Limpiar selección
        ctx.pop("dictamen_selected", None)
        ctx.pop("dictamen_opciones", None)

        return (f"¡Listo! Registré tu carta de dictamen para '{entrada['materia']}'.\n"
                f"Folio: {folio}\n"
                f"Archivo: {str(_DICTAMEN_LOG)}\n"
                "Servicios escolares revisarán tu solicitud. ¿Necesitas algo más?")

    # 2) Si pidió seleccionar materia: "dictamen 2" o "dictamen Nombre Materia"
    m_sel = re.search(DICTAMEN_SELECT_RE, text, flags=re.I | re.X)
    if m_sel:
        # Asegurar que ya listamos opciones antes; si no, las generamos
        opciones = ctx.get("dictamen_opciones")
        if not opciones:
            opciones = _encontrar_materias_dictamen(kuser)
            ctx["dictamen_opciones"] = opciones

        if not opciones:
            return "No tienes materias que requieran dictamen (¡bien!)."

        num = (m_sel.group("num") or "").strip()
        name = (m_sel.group("name") or "").strip()

        elegido = None
        if num:
            try:
                idx = int(num) - 1
                if 0 <= idx < len(opciones):
                    elegido = opciones[idx]
            except ValueError:
                pass

        if not elegido and name:
            nrm = _normaliza(name)
            for opt in opciones:
                if _normaliza(opt.get("materia")) == nrm:
                    elegido = opt
                    break

        if not elegido:
            # Mostrar de nuevo el menú
            out = ["No identifiqué esa opción. Selecciona una de estas materias:\n"]
            for i, r in enumerate(opciones, 1):
                out.append(f"{i}. {r.get('materia', 'Materia')} "
                           f"(Cursada: {r.get('semestre','')}, Calif: {r.get('calificacion','')}, "
                           f"{r.get('semestres_transcurridos',0)} semestres atrás)")
            out.append("\nResponde con:  'dictamen <número>'  o  'dictamen <nombre de la materia>'")
            return "\n".join(out)

        # Guardar selección y pedir carta
        ctx["dictamen_selected"] = elegido
        mat = elegido.get("materia", "la materia seleccionada")
        return (f"Seleccionado dictamen para: {mat}.\n"
                "Ahora envía tu carta de motivos iniciando con:\n"
                "  carta: <explica por qué solicitas el dictamen, compromisos, cómo evitarás reprobación, etc.>\n"
                "Ejemplo:\n"
                "  carta: Solicito dictamen para recursar por motivos de salud...")

    # 1) Inicio del flujo: listar materias con dictamen
    # Preparar listado
    materias_dic = _encontrar_materias_dictamen(kuser)
    if not materias_dic:
        return ("¡Excelente! No tienes materias que requieran dictamen.\n"
                "Si buscas ETS normales, puedes pedir: 'ets'.")

    # Guardar opciones para selección posterior
    ctx["dictamen_opciones"] = materias_dic

    # Si sólo hay una, seleccionarla directamente
    if len(materias_dic) == 1:
        ctx["dictamen_selected"] = materias_dic[0]
        m = materias_dic[0]
        return (f"Tienes una materia que requiere dictamen:\n"
        f"• {m.get('materia','Materia')} "
        f"(Cursada: {m.get('semestre','')}, Calif: {m.get('calificacion','')}, "
        f"{m.get('semestres_transcurridos',0)} semestres atrás)\n\n"
        "TU CARTA DEBE EMPEZAR CON:\n"
        f"  ('carta: <tu texto>') \n"
        "Ejemplo:\n"
        f"  ('carta:') Solicito dictamen debido a... Me comprometo a... He ajustado mi horario para...")


    # Si hay varias, mostrar menú numerado
    out = []
    out.append("MATERIAS QUE REQUIEREN DICTAMEN")
    out.append("=" * 35)
    for i, r in enumerate(materias_dic, 1):
        out.append(f"{i}. {r.get('materia','Materia')}")
        out.append(f"   Semestre cursado: {r.get('semestre','')} "
                   f"({r.get('semestres_transcurridos',0)} semestres atrás)")
        out.append(f"   Calificación: {r.get('calificacion','')}")
        g = r.get("grupo", ""); p = r.get("profesor","")
        if g or p:
            out.append(f"   Grupo original: {g} ({p})")
        out.append("")
    out.append("Selecciona una opción con:")
    out.append("  dictamen <número>   o   dictamen <nombre de la materia>")
    out.append("Luego envía tu carta con:  carta: <tu texto>")
    return "\n".join(out)


# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
