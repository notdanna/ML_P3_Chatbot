import re, unicodedata
def handle(ctx, text):
    return "Proceso de inscripción iniciado (demo)."


Inscripcion_RE = r"""
(?i)\b(
    inscripcion | preinscripcion | reinscripcion | inscrib\w* | reinscrib\w* |
    alta\s+de\s+materias? | carga\s+de\s+materias? | cargar\s+materias? |
    seleccionar\s+materias? | elegir\s+materias? |
    turno | ficha | cita | ventana | periodo |
    fechas?\s+de\s+inscripcion | calendario\s+de\s+inscripcion
)\b
"""

Informacion_personal_RE = r"""
(?i)\b(
    informacion | datos | perfil | personales? | contacto | medicos? |
    domicilio | direccion | telefono | celular | correo | email |
    curp | rfc | nss | imss |
    seguro\s+facultativo | emergencia | alergias | tipo\s+de\s+sangre
)\b
"""
