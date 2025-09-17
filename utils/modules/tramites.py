# utils/modules/tramites.py
import re

# ------------------ Disparadores / RE ------------------

TRAMITES_RE = r"""
\b(
    (?:ir\s+a\s+)?                  
    (?:ver|hacer|revisar)?          
    \s*
    (?:tramite?s?|tramiets?|tramtes?|trami+tes?|  
       gestion(?:es)?|
       papeleo|
       solicitud(?:es)?|
       servicio(?:s)?)
)\b
"""

TRAM_SOLICITUD_RE = r"""
\b(
    (?:registrar|levantar|hacer|crear|meter|enviar)?\s*
    solicitud(?:es)?                # "solicitud" / "solicitudes"
    | solicitar                     # "solicitar"
)\b
"""

# Subintención: Seguimiento (ver estado/estatus, dar seguimiento)
TRAM_SEGUIMIENTO_RE = r"""
\b(
    seguimiento
  | (?:dar\s+)?seguimiento\s*(?:a\s+)?    # "dar seguimiento (a ...)"
  | (?:ver|consultar|revisar)\s*(?:el\s*)?(?:estado|estatus)
  | estatus|status
)\b
"""

# Subintención: Citas (agendar/programar/reprogramar/cancelar/ver citas)
TRAM_CITAS_RE = r"""
\b(
    citas?                                     # "cita" / "citas"
  | (?:agendar|programar|reprogramar|cancelar|ver)\s+citas?
)\b
"""

# ------------------ Handler ------------------

def handle(ctx, text):
    # Normalizamos flags de búsqueda
    flags = re.I | re.X

    # Subintenciones primero
    if re.search(TRAM_SOLICITUD_RE, text, flags=flags):
        return ("[Trámites > Solicitud]\n"
                "Aquí podrás **registrar una solicitud**. (WIP)\n"
                "Opciones: volver a 'tramites', 'seguimiento', 'citas'.")

    if re.search(TRAM_SEGUIMIENTO_RE, text, flags=flags):
        return ("[Trámites > Seguimiento]\n"
                "Aquí puedes **consultar el estado** de tu trámite. (WIP)\n"
                "Opciones: volver a 'tramites', 'solicitud', 'citas'.")

    if re.search(TRAM_CITAS_RE, text, flags=flags):
        return ("[Trámites > Citas]\n"
                "Aquí podrás **agendar o consultar citas** relacionadas. (WIP)\n"
                "Opciones: volver a 'tramites', 'solicitud', 'seguimiento'.")

    # Entrada general a la sección de Trámites (mensaje de bienvenida)
    if re.search(TRAMITES_RE, text, flags=flags):
        return ("Hola, esta es la **sección de Trámites**.\n"
                "Aquí puedes consultar **Documentos e información de**:\n"
                "- **Solicitud**\n- **Seguimiento**\n- **Citas**\n\n"
                "Escribe una opción (por ejemplo: 'solicitud', 'seguimiento' o 'citas').")

    # Si tu automáta enruta por RE, quizá este else no sea necesario.
    return "No entendí. Prueba con: 'tramites', 'solicitud', 'seguimiento' o 'citas'."

# Mantener el estado igual que otros módulos (ajústalo a tu flujo)
NEXT_STATE = "AUTH_OK"
ALLOWED_STATES = {"AUTH_OK"}
