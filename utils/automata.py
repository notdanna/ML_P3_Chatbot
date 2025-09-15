# utils/automata.py
"""
Autómata que carga INTENCIONES desde los módulos en utils.modules.*
- NO define expresiones: toma todas las variables que terminen en *_RE de cada módulo.
- Asocia cada *_RE al handler del mismo módulo: handle(ctx, text).
- Estado siguiente:
    * Si el módulo tiene NEXT_STATE, se usa.
    * Si no, se usa STATE_BY_MODULE.get(nombre_modulo) o "START" por defecto.
API:
    - create_automata() -> Automata
    - get_automata() -> Automata (singleton)
    - process_input(text: str) -> str
"""

from __future__ import annotations
import re
import pkgutil
import importlib
import unicodedata
from typing import Callable, List, Optional, Tuple, Pattern

# -------------------- Utils --------------------
def norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s

def compile_re(pat: str) -> Pattern:
    flags = re.I | re.X
    return re.compile(pat, flags)

STATE_BY_MODULE = {
    "iniciarSesion": "AUTH",
    "cerrarSesion": "END",
}

# -------------------- Contexto --------------------
class Context(dict):
    user: Optional[str] = None
    state: str = "START"

# -------------------- Autómata --------------------
class Automata:
    def __init__(self) -> None:
        self.ctx: Context = Context()
        # (regex, handler, next_state, origin_module)
        self._routes: List[Tuple[Pattern, Callable[[Context, str], str], str, str]] = []
        self._fallback: Optional[Callable[[Context, str], str]] = None
        self._load_routes_from_modules()
        self.fallback(lambda ctx, text:
            "No entendí tu solicitud. Prueba con comandos como 'iniciar sesión', "
            "'info académica', 'trámites', 'inscripción', 'materias' o 'cerrar sesión'.")

    # Descubre utils.modules.*, importa, y registra *_RE -> handle
    def _load_routes_from_modules(self) -> None:
        pkg_name = "utils.modules"
        try:
            pkg = importlib.import_module(pkg_name)
        except Exception as e:
            raise RuntimeError(f"No pude importar {pkg_name}: {e}")

        for finder, mod_name, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(mod_name)
            except Exception:
                continue  # si un módulo falla al importar, lo saltamos

            short_name = mod_name.rsplit(".", 1)[-1]

            # Estado siguiente por módulo (sobrescribe si el módulo define NEXT_STATE)
            next_state = getattr(mod, "NEXT_STATE", STATE_BY_MODULE.get(short_name, "START"))

            # Handler requerido
            handler = getattr(mod, "handle", None)
            if not callable(handler):
                continue  # si no hay handle, no registramos nada

            # Recolectar todas las variables *_RE como patrones
            for attr, value in vars(mod).items():
                if attr.endswith("_RE") and isinstance(value, str) and value.strip():
                    try:
                        rx = compile_re(value)
                        self._routes.append((rx, handler, next_state, short_name))
                    except re.error:
                        # patrón inválido, lo ignoramos
                        continue

        # Si no cargó nada, dejamos al menos algo de diagnóstico
        if not self._routes:
            # fallback mínimo si no se hallaron rutas
            self.fallback(lambda ctx, text:
                "No hay rutas registradas. Asegúrate de definir *_RE y handle(ctx, text) en tus módulos de utils/modules.")

    # API pública
    def route(self, pattern: str, handler: Callable[[Context, str], str], next_state: str = "START", origin: str = "manual") -> None:
        self._routes.append((compile_re(pattern), handler, next_state, origin))

    def fallback(self, handler: Callable[[Context, str], str]) -> None:
        self._fallback = handler

    def step(self, text: str) -> str:
        t = norm(text)
        for rx, fn, nxt, origin in self._routes:
            if rx.search(t):
                out = fn(self.ctx, text)
                self.ctx.state = nxt or self.ctx.state
                return out
        if self._fallback:
            return self._fallback(self.ctx, text)
        return "No hay manejador para tu solicitud."

    def reset(self) -> None:
        self.ctx = Context()

# -------------------- Singleton --------------------
_AUTOMATA_SINGLETON: Optional[Automata] = None

def create_automata() -> Automata:
    return Automata()

def get_automata() -> Automata:
    global _AUTOMATA_SINGLETON
    if _AUTOMATA_SINGLETON is None:
        _AUTOMATA_SINGLETON = Automata()
    return _AUTOMATA_SINGLETON

def process_input(text: str) -> str:
    return get_automata().step(text)
