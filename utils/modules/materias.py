# utils/modules/materias.py
import re
import csv
from pathlib import Path
from collections import defaultdict

# ------------------ Configuración de datos ------------------

# Rutas absolutas a los CSVs
_GRUPOS_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "grupos.csv"
_MATERIAS_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "materias.csv"

# Caché simple en memoria
_GRUPOS_CACHE = None
_MATERIAS_CACHE = None


def _load_grupos():
    """Carga el CSV de grupos y lo deja en caché."""
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


def _load_materias():
    """Carga el CSV de materias y lo deja en caché."""
    global _MATERIAS_CACHE
    if _MATERIAS_CACHE is not None:
        return _MATERIAS_CACHE

    rows = []
    try:
        with open(_MATERIAS_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                rows.append(row)
    except FileNotFoundError:
        rows = []

    _MATERIAS_CACHE = rows
    return _MATERIAS_CACHE


def _datos_disponibles():
    """Verifica que existan los archivos de grupos y materias."""
    grupos = _load_grupos()
    materias = _load_materias()
    
    if not grupos:
        return (False, f"No encuentro el archivo de grupos: '{_GRUPOS_CSV}'")
    if not materias:
        return (False, f"No encuentro el archivo de materias: '{_MATERIAS_CSV}'")
    
    return (True, None)


def _get_materia_info(materia_id, materias_dict):
    """Obtiene información completa de una materia por su ID."""
    materia = materias_dict.get(materia_id, {})
    return {
        'nombre': materia.get('nombre', f'Materia {materia_id}'),
        'clave': materia.get('clave', ''),
        'creditos': materia.get('creditos', ''),
        'area': materia.get('area', '')
    }


def _calcular_disponibilidad(grupos):
    """Calcula estadísticas de disponibilidad de cupos."""
    total_grupos = len(grupos)
    grupos_disponibles = 0
    cupos_totales = 0
    cupos_disponibles = 0
    
    for grupo in grupos:
        try:
            capacidad = int(grupo.get('capacidad', 0))
            inscritos = int(grupo.get('inscritos', 0))
            disponibles = max(0, capacidad - inscritos)
            
            cupos_totales += capacidad
            cupos_disponibles += disponibles
            
            if disponibles > 0:
                grupos_disponibles += 1
        except ValueError:
            continue
    
    return {
        'total_grupos': total_grupos,
        'grupos_disponibles': grupos_disponibles,
        'cupos_totales': cupos_totales,
        'cupos_disponibles': cupos_disponibles,
        'porcentaje_ocupacion': round((cupos_totales - cupos_disponibles) / cupos_totales * 100, 1) if cupos_totales > 0 else 0
    }


def _render_materias_grupos(grupos, materias_dict, stats):
    """Renderiza la lista de materias y grupos con información completa."""
    if not grupos:
        return "No hay grupos disponibles para este periodo."
    
    # Organizar grupos por materia
    por_materia = defaultdict(list)
    for grupo in grupos:
        materia_id = grupo.get('materia_id', '')
        por_materia[materia_id].append(grupo)
    
    out = []
    out.append("MATERIAS Y GRUPOS DISPONIBLES - PERIODO 2025-1")
    out.append("=" * 60)
    out.append(f"Total de grupos: {stats['total_grupos']}")
    out.append(f"Grupos con cupo disponible: {stats['grupos_disponibles']}")
    out.append(f"Cupos disponibles: {stats['cupos_disponibles']}/{stats['cupos_totales']}")
    out.append(f"Ocupacion general: {stats['porcentaje_ocupacion']}%")
    out.append("")
    
    # Ordenar materias por ID
    materias_ordenadas = sorted(por_materia.keys())
    
    for materia_id in materias_ordenadas:
        grupos_materia = por_materia[materia_id]
        info_materia = _get_materia_info(materia_id, materias_dict)
        
        # Encabezado de materia
        out.append(f"[{info_materia['clave']}] {info_materia['nombre']}")
        out.append(f"Area: {info_materia['area']} | Creditos: {info_materia['creditos']}")
        out.append("-" * 50)
        
        # Grupos de la materia
        for grupo in grupos_materia:
            grupo_id = grupo.get('grupo_id', '')
            profesor = grupo.get('profesor', '')
            horario = grupo.get('horario', '')
            turno = grupo.get('turno', '')
            modalidad = grupo.get('modalidad', '')
            salon = grupo.get('salon', '')
            capacidad = grupo.get('capacidad', '0')
            inscritos = grupo.get('inscritos', '0')
            
            try:
                cap_num = int(capacidad)
                ins_num = int(inscritos)
                disponibles = max(0, cap_num - ins_num)
                estado_cupo = f"DISPONIBLE ({disponibles})" if disponibles > 0 else "SIN CUPO"
            except ValueError:
                estado_cupo = "CUPO INDEFINIDO"
            
            out.append(f"  Grupo {grupo_id} - {profesor}")
            out.append(f"    Horario: {horario} ({turno})")
            out.append(f"    Modalidad: {modalidad} | Salon: {salon}")
            out.append(f"    Cupo: {inscritos}/{capacidad} - {estado_cupo}")
            out.append("")
        
        out.append("")  # Separación entre materias
    
    return "\n".join(out)


# ------------------ Disparador / RE ------------------

MATERIAS_RE = r"\b(materia(?:s)?|lista\s+de\s+materias|ver\s+materias|grupos|cupos?)\b"


# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    
    # Verificar disponibilidad de datos
    ok, err = _datos_disponibles()
    if not ok:
        return err
    
    grupos = _load_grupos()
    materias = _load_materias()
    
    # Convertir materias a diccionario para búsqueda rápida
    materias_dict = {m.get('materia_id', ''): m for m in materias}
    
    # Filtrar grupos por periodo actual (2025-1)
    grupos_periodo = [g for g in grupos if g.get('periodo_id', '') == '2025-1']
    
    if not grupos_periodo:
        return ("No encontré grupos disponibles para el periodo actual (2025-1). "
               "¿Quieres 'ver calificaciones', 'info academica', 'tramites' o 'inscripcion'?")
    
    # Calcular estadísticas y renderizar
    stats = _calcular_disponibilidad(grupos_periodo)
    materias_texto = _render_materias_grupos(grupos_periodo, materias_dict, stats)
    
    return (f"{materias_texto}\n\n"
           "¿Quieres 'inscripcion' para inscribirte, 'ver calificaciones' o 'info academica'?")


# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}