import re, unicodedata
from utils.tablasIntencion import INTENTS, SUBINTENTS
# ======================================================
# Helpers de match
# ======================================================
def findall_intents(text: str):
    """Devuelve TODAS las categorías principales que disparan (ordenadas por prioridad)."""
    t = norm(text)
    hits = []
    for name, pattern in INTENTS:
        if re.search(pattern, t, flags=re.I | re.X):
            hits.append(name)
    priority = ["cerrar_sesion","iniciar_sesion","inscripcion","tramites","materias",
                "info_personal","info_academica","afirmacion","salir","regresar"]
    hits.sort(key=lambda k: priority.index(k) if k in priority else 999)
    return hits

def findall_subintents(text: str, main_category: str):
    """Para una categoría principal, devuelve las subcategorías que disparan."""
    t = norm(text)
    subs = SUBINTENTS.get(main_category, [])
    return [name for name, pattern in subs if re.search(pattern, t, flags=re.I | re.X)]

def norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s

