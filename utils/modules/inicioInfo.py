# utils/modules/inicioInfo.py
INICIOINFO_RE = r"\b(inicio\s*info|informacion\s+inicial|bienvenida)\b"
def handle(ctx, text):
    if ctx.get("auth_ok"):
        try:
            with open("/home/miguelg/ML/assig3/ML_P3_Chatbot/resources/infoAlumnos", "r", encoding="utf-8") as f:
                data = f.read()
            return data
        except Exception as e:
            return f"Error leyendo infoAlumnos: {e}"
    return "Para comenzar, di: 'iniciar sesion'."

NEXT_STATE = ""                
ALLOWED_STATES = {"START", "AUTH", "AUTH_OK"}
