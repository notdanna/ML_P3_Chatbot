# -*- coding: utf-8 -*-
"""
SAES — Regex por categorías y subcategorías (formato simple) + pruebas + REPL

• Normaliza: minúsculas, sin acentos, espacios colapsados.
• Categorías: iniciar/cerrar sesión, inscripción, info personal, materias, trámites, info académica.
• Subcategorías (ejemplos):
    - Materias: cupos | profesor | horario | materia
    - Trámites: dictamen | ets | info (otros tramites)
    - Info académica: kardex | horario | calificaciones
• Búsqueda con flags re.I | re.X (importante: re.X ignora espacios en el patrón).

Diseño: cobertura amplia por “palabras gatillo”. Tu autómata decide después.
"""

import re, unicodedata

# Normalización para evitar problemas con mayúsculas, acentos, espacios, etc.
def norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s


Iniciar_Sesion_RE = r"""
(?i)\b(
    iniciar\s+sesion | entrar | acceder | ingresar | conectar(?:me|se)? |
    meterme | abrir | login | log\s*in | loguear(?:me|se)? | logear(?:me|se)? |
    sign\s*in | usuario\s*y\s*contrasena | clave\s*de\s*acceso | password | saes
)\b
"""

Cerrar_Sesion_RE = r"""
(?i)\b(
    cerrar\s+sesion | terminar\s+sesion | salir | logout | sign\s*out |
    desconectar(?:me|se)? | cerrar\s+cuenta
)\b
"""

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

# ======================================================
# SUBCATEGORÍAS
# ======================================================
# Materias
Materias_cupos_RE = r"(?i)\b( cupo[s]? | lugar[es]? | espacio[s]? | disponibilidad )\b"
Materias_profesor_RE = r"(?i)\b( profesor[es]? | docente[s]? | maestro[s]? | catedratico[s]? | titular[es]? )\b"
Materias_horario_RE = r"(?i)\b( horario[s]? | hora[s]? )\b"
Materias_materia_RE = r"(?i)\b( materia[s]? | asignatura[s]? | clave(?:\s+de\s+materia)? | nrc | credito[s]? | plan\s+de\s+estudios | optativa[s]? | obligatoria[s]? )\b"

# Trámites
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

# Información académica
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

# Opcionales generales
Afirmacion_RE = r"(?i)\b( si | sip | claro | por\s+supuesto | definitivamente | de\s+acuerdo | ok | correcto | gracias )\b"
Salir_RE      = r"(?i)\b( salir | me\s+equivoque | perdon | adios | ups | sorry | error | deseo\s+(?:salir|interrumpir) )\b"
Regresar_RE   = r"(?i)\b( regresar | volver | atras | menu | inicio | empezar | comenzar | otra\s+consulta )\b"

# ======================================================
# Tablas de intención
# ======================================================
INTENTS = [
    ("cerrar_sesion", Cerrar_Sesion_RE),
    ("iniciar_sesion", Iniciar_Sesion_RE),
    ("inscripcion", Inscripcion_RE),
    ("tramites", Tramites_RE),
    ("materias", Materias_RE),
    ("info_personal", Informacion_personal_RE),
    ("info_academica", Informacion_academica_RE),
    ("afirmacion", Afirmacion_RE),
    ("salir", Salir_RE),
    ("regresar", Regresar_RE),
]

SUBINTENTS = {
    "materias": [
        ("materias_cupos", Materias_cupos_RE),
        ("materias_profesor", Materias_profesor_RE),
        ("materias_horario", Materias_horario_RE),
        ("materias_materia", Materias_materia_RE),
    ],
    "tramites": [
        ("tramites_dictamen", Tramites_dictamen_RE),
        ("tramites_ets", Tramites_ets_RE),
        ("tramites_info", Tramites_info_RE),
    ],
    "info_academica": [
        ("info_acad_kardex", Informacion_academica_kardex_RE),
        ("info_acad_horario", Informacion_academica_horario_RE),
        ("info_acad_calificaciones", Informacion_academica_calificaciones_RE),
    ],
}

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

# ======================================================
# PRUEBAS RÁPIDAS
# ======================================================
if __name__ == "__main__":
    tests = [
        # Iniciar / Cerrar sesión
        "Quiero iniciar sesión en SAES",
        "login saes",
        "cerrar mi sesión",
        "logout",

        # Inscripción
        "reinscripcion y ficha",
        "alta de materias",
        "fechas de inscripcion",
        "me quiero inscribir",

        # Info personal
        "actualizar mi telefono y correo",
        "cambiar direccion y curp",

        # Materias
        "ver cupos",
        "profesores y horarios",
        "clave de materia y creditos",
        "materias",

        # Trámites
        "requisitos para servicio social",
        "dictamen de equivalencia",
        "convocatoria de becas",
        "ETS y extraordinario",

        # Info académica
        "descargar boleta de calificaciones",
        "kardex y adeudos",
        "mi horario",

        # Control
        "sí claro",
        "me equivoque, deseo salir",
        "volver al menú",
    ]

    print("=== PRUEBAS RÁPIDAS (categoría y subcategorías) ===")
    for s in tests:
        mains = findall_intents(s)
        subs = {m: findall_subintents(s, m) for m in mains}
        print(f"- {s!r} -> mains={mains} subs={subs}")

    # REPL
    print("\nSAES Regex — escribe una frase y te digo categorías y subcategorías. Ctrl+C para salir.\n")
    try:
        while True:
            s = input("> ")
            mains = findall_intents(s)
            subs = {m: findall_subintents(s, m) for m in mains}
            if not mains:
                print("→ Sin coincidencias")
            else:
                print("→ Categorías:", mains)
                print("→ Subcategorías:", {k: v for k, v in subs.items() if v})
    except KeyboardInterrupt:
        print("\nAdiós.")
