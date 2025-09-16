# utils/modules/ets.py
import re
import csv
from pathlib import Path
from collections import defaultdict

# ------------------ Configuración de datos ------------------

# Rutas absolutas a los CSVs
_KARDEX_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "kardex.csv"
_GRUPOS_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "grupos.csv"
_MATERIAS_CSV = Path(__file__).resolve().parents[2] / "resources" / "data" / "materias.csv"

# Caché simple en memoria
_KARDEX_CACHE = None
_GRUPOS_CACHE = None
_MATERIAS_CACHE = None


def _load_kardex():
    """Carga el CSV del kardex y lo deja en caché."""
    global _KARDEX_CACHE
    if _KARDEX_CACHE is not None:
        return _KARDEX_CACHE

    rows = []
    has_boleta = False
    try:
        with open(_KARDEX_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                rows.append(row)
            if rows:
                has_boleta = "boleta" in rows[0]
    except FileNotFoundError:
        rows = []
        has_boleta = False

    _KARDEX_CACHE = (rows, has_boleta)
    return _KARDEX_CACHE


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
    """Verifica que existan los archivos necesarios."""
    kardex, _ = _load_kardex()
    if not kardex:
        return (False, f"No encuentro el archivo de kardex: '{_KARDEX_CSV}'")
    return (True, None)


def _calcular_diferencia_semestres(semestre_reprobado, semestre_actual="2025-1"):
    """Calcula la diferencia en semestres entre cuando se reprobó y el semestre actual."""
    try:
        # Parsear semestre reprobado (ej: "2023-2")
        año_reprobado, periodo_reprobado = semestre_reprobado.split("-")
        año_reprobado = int(año_reprobado)
        periodo_reprobado = int(periodo_reprobado)
        
        # Parsear semestre actual (ej: "2025-1")
        año_actual, periodo_actual = semestre_actual.split("-")
        año_actual = int(año_actual)
        periodo_actual = int(periodo_actual)
        
        # Calcular diferencia en semestres
        # Cada año tiene 2 semestres
        semestres_reprobado = (año_reprobado * 2) + periodo_reprobado
        semestres_actual = (año_actual * 2) + periodo_actual
        
        return semestres_actual - semestres_reprobado
    
    except (ValueError, IndexError):
        return 0  # Si no se puede parsear, asumir que es reciente


def _encontrar_materias_reprobadas(kardex_usuario):
    """Identifica materias reprobadas (calificación < 6) del kardex del usuario."""
    reprobadas = []
    
    for materia in kardex_usuario:
        calif_str = materia.get("calificacion", "").strip()
        if calif_str == "":
            continue  # Materias sin calificación (cursando)
        
        try:
            calif = float(calif_str)
            if calif < 6:  # Calificación reprobatoria
                # Calcular si requiere dictamen (más de 3 semestres)
                semestre = materia.get("semestre", "")
                semestres_transcurridos = _calcular_diferencia_semestres(semestre)
                
                # Agregar información de dictamen a la materia
                materia_info = materia.copy()
                materia_info['requiere_dictamen'] = semestres_transcurridos > 3
                materia_info['semestres_transcurridos'] = semestres_transcurridos
                
                reprobadas.append(materia_info)
        except ValueError:
            continue  # Calificaciones no numéricas
    
    return reprobadas


def _get_info_materia_por_nombre(nombre_materia, materias_dict):
    """Busca información de una materia por su nombre completo."""
    for materia_id, info in materias_dict.items():
        if info.get('nombre', '').lower() == nombre_materia.lower():
            return info
    return {}


def _buscar_grupos_disponibles(nombre_materia, grupos):
    """Busca grupos disponibles para una materia específica por nombre."""
    grupos_disponibles = []
    
    # Primero necesitamos encontrar el materia_id correspondiente
    materias = _load_materias()
    materias_dict = {m.get('materia_id', ''): m for m in materias}
    
    materia_id_encontrado = None
    for materia_id, info in materias_dict.items():
        if info.get('nombre', '').lower() == nombre_materia.lower():
            materia_id_encontrado = materia_id
            break
    
    if not materia_id_encontrado:
        return []
    
    # Buscar grupos de esa materia en el periodo actual
    for grupo in grupos:
        if (grupo.get('materia_id', '') == materia_id_encontrado and 
            grupo.get('periodo_id', '') == '2025-1'):
            try:
                capacidad = int(grupo.get('capacidad', 0))
                inscritos = int(grupo.get('inscritos', 0))
                if capacidad > inscritos:  # Tiene cupo disponible
                    grupos_disponibles.append(grupo)
            except ValueError:
                continue
    
    return grupos_disponibles


def _render_ets(reprobadas, grupos, materias_dict):
    """Renderiza la información de ETS para materias reprobadas."""
    if not reprobadas:
        return ("¡Excelente! No tienes materias reprobadas que requieran ETS.\n"
               "Todas tus materias han sido aprobadas satisfactoriamente.")
    
    # Separar materias por tipo
    ets_normales = [m for m in reprobadas if not m.get('requiere_dictamen', False)]
    con_dictamen = [m for m in reprobadas if m.get('requiere_dictamen', False)]
    
    out = []
    out.append("EXAMENES A TITULO DE SUFICIENCIA (ETS)")
    out.append("=" * 50)
    out.append(f"Total de materias reprobadas: {len(reprobadas)}")
    out.append(f"• ETS normales: {len(ets_normales)}")
    out.append(f"• ETS con DICTAMEN: {len(con_dictamen)}")
    out.append("")
    
    # Mostrar ETS normales primero
    if ets_normales:
        out.append("ETS NORMALES (menos de 3 semestres reprobadas)")
        out.append("-" * 45)
        for i, materia in enumerate(ets_normales, 1):
            nombre = materia.get("materia", "Materia desconocida")
            semestre = materia.get("semestre", "")
            grupo_original = materia.get("grupo", "")
            profesor_original = materia.get("profesor", "")
            calif = materia.get("calificacion", "")
            semestres_transcurridos = materia.get("semestres_transcurridos", 0)
            
            out.append(f"{i}. {nombre}")
            out.append(f"   Semestre cursado: {semestre} ({semestres_transcurridos} semestres atrás)")
            out.append(f"   Grupo original: {grupo_original} ({profesor_original})")
            out.append(f"   Calificacion reprobatoria: {calif}")
            
            # Buscar grupos disponibles para recuperar la materia
            grupos_disponibles = _buscar_grupos_disponibles(nombre, grupos)
            
            if grupos_disponibles:
                out.append("   GRUPOS DISPONIBLES PARA RECUPERAR:")
                for grupo in grupos_disponibles[:2]:  # Máximo 2 grupos para ahorrar espacio
                    grupo_id = grupo.get('grupo_id', '')
                    profesor = grupo.get('profesor', '')
                    horario = grupo.get('horario', '')
                    modalidad = grupo.get('modalidad', '')
                    salon = grupo.get('salon', '')
                    capacidad = grupo.get('capacidad', '0')
                    inscritos = grupo.get('inscritos', '0')
                    
                    try:
                        disponibles = int(capacidad) - int(inscritos)
                        out.append(f"     - {grupo_id}: {profesor}")
                        out.append(f"       {horario} ({modalidad}) | Cupo: {disponibles}")
                    except ValueError:
                        out.append(f"     - {grupo_id}: {profesor} | {horario}")
            else:
                out.append("   SIN GRUPOS DISPONIBLES en el periodo actual")
            
            out.append("")
    
    # Mostrar ETS con DICTAMEN
    if con_dictamen:
        out.append("*** ETS CON DICTAMEN REQUERIDO (más de 3 semestres reprobadas) ***")
        out.append("-" * 65)
        out.append("¡ATENCION! Estas materias requieren DICTAMEN de servicios escolares")
        out.append("")
        
        for i, materia in enumerate(con_dictamen, 1):
            nombre = materia.get("materia", "Materia desconocida")
            semestre = materia.get("semestre", "")
            grupo_original = materia.get("grupo", "")
            profesor_original = materia.get("profesor", "")
            calif = materia.get("calificacion", "")
            semestres_transcurridos = materia.get("semestres_transcurridos", 0)
            
            out.append(f"{i}. {nombre}")
            out.append(f"   Semestre cursado: {semestre} ({semestres_transcurridos} semestres atrás)")
            out.append(f"   Grupo original: {grupo_original} ({profesor_original})")
            out.append(f"   Calificacion reprobatoria: {calif}")
            out.append(f"   *** REQUIERE DICTAMEN DE SERVICIOS ESCOLARES ***")
            
            # Para materias con dictamen, aún mostrar opciones pero con advertencia
            grupos_disponibles = _buscar_grupos_disponibles(nombre, grupos)
            if grupos_disponibles:
                out.append("   GRUPOS DISPONIBLES (previa autorización):")
                for grupo in grupos_disponibles[:1]:  # Solo 1 grupo para ahorrar espacio
                    grupo_id = grupo.get('grupo_id', '')
                    profesor = grupo.get('profesor', '')
                    horario = grupo.get('horario', '')
                    modalidad = grupo.get('modalidad', '')
                    
                    out.append(f"     - {grupo_id}: {profesor} | {horario} ({modalidad})")
            
            out.append("")
    
    # Información general
    out.append("INFORMACION IMPORTANTE:")
    out.append("-" * 25)
    if ets_normales:
        out.append("ETS NORMALES:")
        out.append("• Puedes inscribirte directamente si hay cupo")
        out.append("• También puedes solicitar examen especial")
    
    if con_dictamen:
        out.append("")
        out.append("ETS CON DICTAMEN:")
        out.append("• OBLIGATORIO solicitar dictamen en servicios escolares")
        out.append("• Presenta tu kardex y solicita autorización")
        out.append("• Solo después del dictamen puedes inscribirte")
        out.append("• Proceso puede tomar varios días hábiles")
    
    out.append("")
    out.append("• Consulta fechas límite en servicios escolares")
    out.append("• Revisa horarios para evitar empalmes")
    out.append("")
    
    return "\n".join(out)


# ------------------ Disparadores / RE ------------------

# Expresiones más amplias para capturar diferentes formas de solicitar ETS
ETS_RE = r"\b(ets|reprobadas?|reprobado?s?|sin\s+pasar|extras?|examenes?\s+(especiales?|titulo|suficiencia)|materias?\s+no\s+aprobadas?)\b"

REPROBADAS_RE = r"\b(que\s+materias?\s+(reprobe|reprobé|no\s+pase)|cuales?\s+(reprobe|reprobé)|mis\s+reprobadas?)\b"


# ------------------ Handler ------------------

def handle(ctx, text):
    if not ctx.get("auth_ok"):
        return "Primero inicia sesión."
    
    # Verificar disponibilidad de datos
    ok, err = _datos_disponibles()
    if not ok:
        return err
    
    kardex, has_boleta = _load_kardex()
    boleta = str(ctx.get("user", "")).strip()
    
    if not has_boleta:
        return ("El archivo de kardex no tiene columna 'boleta'. "
               "No puedo identificar tus materias reprobadas específicas.")
    
    # Filtrar kardex por usuario
    kardex_usuario = [r for r in kardex if r.get("boleta", "").strip() == boleta]
    
    if not kardex_usuario:
        return (f"No encontré tu historial académico (boleta {boleta}). "
               "Verifica con servicios escolares.")
    
    # Encontrar materias reprobadas
    reprobadas = _encontrar_materias_reprobadas(kardex_usuario)
    
    # Cargar datos adicionales para mostrar opciones
    grupos = _load_grupos()
    materias = _load_materias()
    materias_dict = {m.get('materia_id', ''): m for m in materias}
    
    # Renderizar información de ETS
    ets_info = _render_ets(reprobadas, grupos, materias_dict)
    
    return (f"{ets_info}\n\n"
           "¿Quieres ver 'materias' disponibles, 'info academica' o 'ver calificaciones'?")


# Mantener el estado de autenticado
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}