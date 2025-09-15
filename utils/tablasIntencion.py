from modules.cerrarSesion import *
from modules.infoacademica import *
from modules.infopersonal import *
from modules.iniciarSesion import *
from modules.inicioInfo import *
from modules.inscripcion import *
from modules.materias import *
from modules.opcionesGenerales import *
from modules.tramites import *
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
