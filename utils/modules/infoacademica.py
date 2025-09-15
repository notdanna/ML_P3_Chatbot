import re, unicodedata
def handle(ctx, text):
    return "Tu info académica (demo)."
Informacion_academica_RE = r"""
(?i)\b(
    kardex |
    boleta(?:\s+de\s+(?:calificaciones|evaluacion))? |
    calificacion(?:es)? | califs? | notas? |
    promedio(?:\s+(?:general|acumulado))? |
    historial\s+academico |
    adeudo[s]? | deuda[s]? | pago(?:s)?\s+pendiente(?:s)? |
    faltas? | inasistencias? |
    horario[s]?
)\b
"""
# Subcategorias
Informacion_academica_kardex_RE = r"(?i)\b( kardex )\b"
Informacion_academica_horario_RE = r"(?i)\b( horario[s]? )\b"
Informacion_academica_calificaciones_RE = r"""
(?i)\b(
    calificacion(?:es)? | califs? | notas? |
    boleta(?:\s+de\s+(?:calificaciones|evaluacion))? |
    promedio(?:\s+(?:general|acumulado))? | historial\s+academico |
    adeudo[s]? | deuda[s]? | pago(?:s)?\s+pendiente(?:s)?
)\b
"""
