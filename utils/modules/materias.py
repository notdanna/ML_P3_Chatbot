import re, unicodedata
def handle(ctx, text):
    return "Mostrando catálogo de materias (demo)."


Materias_RE = r"""
(?i)\b(
    materia[s]? | clase[s]? | asignatura[s]? | grupo[s]? |
    oferta\s+academica | horario[s]? |
    profesor[es]? | docente[s]? | maestro[s]? | catedratico[s]? | titular[es]? |
    cupo[s]? | lugar[es]? | espacio[s]? | disponibilidad |
    clave(?:\s+de\s+materia)? | credito[s]? | nrc |
    plan\s+de\s+estudios | optativa[s]? | obligatoria[s]? |
    turno | semestre | salon | aula
)\b
"""
# Subcategorias
Materias_cupos_RE = r"(?i)\b( cupo[s]? | lugar[es]? | espacio[s]? | disponibilidad )\b"
Materias_profesor_RE = r"(?i)\b( profesor[es]? | docente[s]? | maestro[s]? | catedratico[s]? | titular[es]? )\b"
Materias_horario_RE = r"(?i)\b( horario[s]? | hora[s]? )\b"
Materias_materia_RE = r"(?i)\b( materia[s]? | asignatura[s]? | clave(?:\s+de\s+materia)? | nrc | credito[s]? | plan\s+de\s+estudios | optativa[s]? | obligatoria[s]? )\b"
