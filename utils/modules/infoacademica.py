# utils/modules/infoacademica.py
import re
import csv
from pathlib import Path
from collections import defaultdict

# ------------------ Configuración de datos ------------------

# Ruta absoluta al CSV: <PROJECT_ROOT>/resources/data/kardex.csv
_CSV_PATH = Path(__file__).resolve().parents[2] / "resources" / "data" / "kardex.csv"

# Caché simple en memoria
_KARDEX_CACHE = None


def _load_kardex():
    """Carga el CSV del kardex y lo deja en caché.
    Devuelve (rows:list[dict], has_boleta:bool)
    """
    global _KARDEX_CACHE
    if _KARDEX_CACHE is not None:
        return _KARDEX_CACHE

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

    _KARDEX_CACHE = (rows, has_boleta)
    return _KARDEX_CACHE


def _kardex_disponible():
    """Verifica que exista el kardex cargable."""
    rows, _ = _load_kardex()
    if not rows:
        return (False,
                f"No encuentro el kardex o el archivo está vacío: '{_CSV_PATH}'. "
                "Asegúrate de crearlo con encabezados "
                "'boleta,semestre,materia,grupo,profesor,horario,calificacion'.")
    return (True, None)


def _calcular_estadisticas(rows):
    """Calcula estadísticas del kardex: promedio, materias cursadas, aprobadas, etc."""
    if not rows:
        return {
            "total_materias": 0,
            "materias_aprobadas": 0,
            "materias_reprobadas": 0,
            "materias_cursando": 0,
            "promedio": 0.0,
            "creditos_cursados": 0
        }
    
    calificaciones = []
    aprobadas = 0
    reprobadas = 0
    cursando = 0
    
    for row in rows:
        calif_str = row.get("calificacion", "").strip()
        if calif_str == "":
            cursando += 1
        else:
            try:
                calif = float(calif_str)
                calificaciones.append(calif)
                if calif >= 6:
                    aprobadas += 1
                else:
                    reprobadas += 1
            except ValueError:
                cursando += 1
    
    promedio = sum(calificaciones) / len(calificaciones) if calificaciones else 0.0
    
    return {
        "total_materias": len(rows),
        "materias_aprobadas": aprobadas,
        "materias_reprobadas": reprobadas,
        "materias_cursando": cursando,
        "promedio": round(promedio, 2),
        "creditos_cursados": aprobadas * 8  # Asumiendo 8 créditos por materia
    }


def _render_kardex(rows, stats):
    """Convierte el kardex a un texto legible organizado por semestre."""
    if not rows:
        return "No hay materias registradas en el kardex."
    
    # Organizar por semestre
    por_semestre = defaultdict(list)
    for row in rows:
        semestre = row.get("semestre", "Sin semestre")
        por_semestre[semestre].append(row)
    
    # Renderizar
    out = []
    out.append("RESUMEN ACADEMICO")
    out.append("=" * 50)
    out.append(f"Promedio general: {stats['promedio']}")
    out.append(f"Materias aprobadas: {stats['materias_aprobadas']}")
    out.append(f"Materias reprobadas: {stats['materias_reprobadas']}")
    out.append(f"Materias cursando: {stats['materias_cursando']}")
    out.append(f"Creditos acumulados: {stats['creditos_cursados']}")
    out.append("")
    out.append("KARDEX POR SEMESTRE")
    out.append("=" * 50)
    out.append("")
    
    # Ordenar semestres
    semestres_ordenados = sorted(por_semestre.keys())
    
    for semestre in semestres_ordenados:
        materias = por_semestre[semestre]
        out.append(f"[{semestre.upper()}]")
        out.append("-" * 30)
        
        for materia in materias:
            nombre = materia.get("materia", "Materia")
            grupo = materia.get("grupo", "")
            profesor = materia.get("profesor", "")
            horario = materia.get("horario", "")
            calif = materia.get("calificacion", "")
            
            linea = f"  - {nombre}"
            
            # Añadir detalles
            detalles = []
            if grupo:
                detalles.append(f"Grupo {grupo}")
            if profesor:
                detalles.append(f"Prof. {profesor}")
            if horario:
                detalles.append(horario)
            
            if detalles:
                linea += f" ({', '.join(detalles)})"
            
            # Calificación
            if calif == "":
                linea += " - CURSANDO"
            else:
                try:
                    calif_num = float(calif)
                    if calif_num >= 6:
                        linea += f" - APROBADO ({calif})"
                    else:
                        linea += f" - REPROBADO ({calif})"
                except ValueError:
                    linea += f" - {calif}"
            
            out.append(linea)
        
        out.append("")  # Línea en blanco entre semestres
    
    return "\n".join(out)


# ------------------ Disparador / RE ------------------

INFOACAD_RE = r"\b(info(\s+academica)?|kardex|historial\s+academico)\b"


# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    
    # Verificar disponibilidad del kardex
    ok, err = _kardex_disponible()
    if not ok:
        return err

    rows, has_boleta = _load_kardex()
    boleta = str(ctx.get("user", "")).strip()

    if has_boleta:
        # Filtrar por la boleta del usuario
        kardex_usuario = [r for r in rows if r.get("boleta", "").strip() == boleta]
        if not kardex_usuario:
            return (f"No encontré información académica para tu boleta {boleta}. "
                   "Verifica con servicios escolares. "
                   "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")
        
        # Calcular estadísticas y renderizar
        stats = _calcular_estadisticas(kardex_usuario)
        kardex_texto = _render_kardex(kardex_usuario, stats)
        
        return (f"{kardex_texto}\n\n"
                "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")
    
    else:
        # Modo compatible: el CSV no tiene 'boleta' -> mostrar información general

        
        stats = _calcular_estadisticas(rows)
        kardex_texto = _render_kardex(rows, stats)  # Mostrar TODAS las materias
        
        return (f"\n\n{kardex_texto}\n\n"
                "¿Quieres 'ver calificaciones', 'materias', 'tramites' o 'inscripcion'?")


# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}