import re, unicodedata
def handle(ctx, text):
    return "Gestión de trámites (demo): constancia, historial, etc."
Tramites_RE = r"""
(?i)\b(
    tramite[s]? |
    dictamen(?:\s+de\s+(?:reingreso|equivalencia))? |
    ets\b |
    baja(?:\s+(?:temporal|definitiva))? |
    servicio\s+social |
    titulacion |
    practicas?\s+profesionales? |
    beca[s]? |
    certificado[s]? |
    constancia[s]? |
    revalidacion | equivalencia[s]? |
    requisitos? | formato | formulario | cita | fechas? | convocatoria
)\b
"""
#Subcategorias
Tramites_dictamen_RE = r"(?i)\b( dictamen(?:\s+de\s+(?:reingreso|equivalencia))? )\b"
Tramites_ets_RE = r"(?i)\b( ets\b | examen(?:es)?\s+extraordinario[s]? | titulo\s+de\s+suficiencia )\b"
Tramites_info_RE = r"""
(?i)\b(
    tramite[s]? | servicio\s+social | titulacion | practicas?\s+profesionales? |
    beca[s]? | certificado[s]? | constancia[s]? |
    revalidacion | equivalencia[s]? |
    requisitos? | formato | formulario | cita | fechas? | convocatoria | baja(?:\s+(?:temporal|definitiva))?
)\b
"""
