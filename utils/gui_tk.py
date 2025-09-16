# File: utils/gui_tk.py
# -*- coding: utf-8 -*-
"""
GUI mínima y robusta para tu autómata usando Tkinter (stdlib).
- No requiere dependencias externas (ideal si PyQt5 te dio problemas).
- Muestra historial, estado actual, entrada con Enter para enviar, y acciones útiles.
- Se integra con tu autómata via `from utils.automata import get_automata`.

Uso sugerido:
    from utils.gui_tk import run_gui
    run_gui()

Atajos:
- Enter: enviar
- Shift+Enter: salto de línea en el cuadro de texto de entrada
- Ctrl+L: limpiar entrada
- Ctrl+R: resetear sesión (estado del autómata)
- Ctrl+S: exportar historial a archivo .txt
"""
from __future__ import annotations
import datetime as _dt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    # Importa el singleton del autómata tal como lo tienes
    from utils.automata import get_automata
except Exception as e:  # Mensaje más claro si falla el import
    raise RuntimeError(f"No pude importar utils.automata.get_automata: {e}")


class _ChatGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SAES CHAT — GUI")
        self.root.minsize(720, 520)

        # Fuente monoespaciada opcional para mejor alineación
        self._font_ui = ("JetBrains Mono", 10)
        self._font_msg = ("JetBrains Mono", 11)

        # Autómata (singleton)
        self.auto = get_automata()

        # ====== Layout principal ======
        self._build_menu()
        self._build_header()
        self._build_console()
        self._build_input()
        self._bind_shortcuts()

        # Mensaje de bienvenida
        self._append("system", "SAES CHAT listo. Escribe 'salir' para terminar o usa el menú.")
        self._refresh_state()

    # ---------- UI builders ----------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        m_chat = tk.Menu(menubar, tearoff=False)
        m_chat.add_command(label="Resetear sesión (Ctrl+R)", command=self._reset_session)
        m_chat.add_separator()
        m_chat.add_command(label="Exportar historial… (Ctrl+S)", command=self._export)
        m_chat.add_separator()
        m_chat.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Chat", menu=m_chat)

        m_ver = tk.Menu(menubar, tearoff=False)
        m_ver.add_command(label="Copiar estado actual", command=self._copy_state)
        menubar.add_cascade(label="Ver", menu=m_ver)

        self.root.config(menu=menubar)

    def _build_header(self) -> None:
        top = ttk.Frame(self.root, padding=(12, 8))
        top.pack(side=tk.TOP, fill=tk.X)

        self.state_var = tk.StringVar(value="STATE: START")
        self.user_var = tk.StringVar(value="USER: –")

        lbl_state = ttk.Label(top, textvariable=self.state_var, font=self._font_ui)
        lbl_user = ttk.Label(top, textvariable=self.user_var, font=self._font_ui)

        lbl_state.pack(side=tk.LEFT)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        lbl_user.pack(side=tk.LEFT)

    def _build_console(self) -> None:
        mid = ttk.Frame(self.root, padding=(12, 0))
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.txt = tk.Text(
            mid,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=18,
            font=self._font_msg,
            padx=8,
            pady=8,
        )
        sb = ttk.Scrollbar(mid, command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)

        self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_input(self) -> None:
        bot = ttk.Frame(self.root, padding=(12, 8))
        bot.pack(side=tk.BOTTOM, fill=tk.X)

        self.entry = tk.Text(bot, height=3, font=self._font_msg)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_send = ttk.Button(bot, text="Enviar", command=self._on_send)
        btn_send.pack(side=tk.LEFT, padx=(8, 0))

    def _bind_shortcuts(self) -> None:
        # Enter => enviar; Shift+Enter => salto de línea
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Shift-Return>", lambda e: None)

        # Ctrl+L: limpiar entrada
        self.entry.bind("<Control-l>", self._clear_entry)

        # Ctrl+R: reset sesión
        self.root.bind("<Control-r>", lambda e: self._reset_session())

        # Ctrl+S: exportar historial
        self.root.bind("<Control-s>", lambda e: self._export())

    # ---------- Helpers ----------
    def _append(self, who: str, text: str) -> None:
        ts = _dt.datetime.now().strftime("%H:%M:%S")
        who_tag = {
            "user": "Tú",
            "bot": "SAES",
            "system": "Sistema",
        }.get(who, who)

        self.txt.configure(state=tk.NORMAL)
        self.txt.insert(tk.END, f"[{ts}] {who_tag}: {text}\n")
        self.txt.configure(state=tk.DISABLED)
        self.txt.see(tk.END)

    def _refresh_state(self) -> None:
        st = getattr(self.auto.ctx, "state", "START")
        usr = getattr(self.auto.ctx, "user", None) or self.auto.ctx.get("user") or "–"
        self.state_var.set(f"STATE: {st}")
        self.user_var.set(f"USER: {usr}")

    def _on_return(self, event: tk.Event) -> str:
        # Si hay Shift, dejamos que inserte salto de línea
        if event.state & 0x0001:  # Shift mask
            return "break"  # prevenimos el comportamiento por defecto de Tk que duplica el salto
        self._on_send()
        return "break"

    def _clear_entry(self, *_):
        self.entry.delete("1.0", tk.END)

    def _export(self) -> None:
        try:
            path = filedialog.asksaveasfilename(
                title="Exportar historial",
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            )
            if not path:
                return
            content = self.txt.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Exportado", f"Historial guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No pude exportar: {e}")

    def _copy_state(self) -> None:
        try:
            st = getattr(self.auto.ctx, "state", "START")
            self.root.clipboard_clear()
            self.root.clipboard_append(st)
            messagebox.showinfo("Copiado", f"STATE actual: {st}")
        except Exception as e:
            messagebox.showerror("Error", f"No pude copiar: {e}")

    def _reset_session(self) -> None:
        # Resetea contexto del autómata
        try:
            self.auto.reset()
        except Exception as e:
            messagebox.showerror("Error", f"No pude resetear el autómata: {e}")
            return
        self._append("system", "Sesión reseteada. STATE=START, USER=–")
        self._refresh_state()

    # ---------- Core ----------
    def _on_send(self) -> None:
        text = self.entry.get("1.0", tk.END).strip()
        if not text:
            return

        # Comandos rápidos opcionales
        if text.lower() in {"salir", "exit", "quit"}:
            self.root.quit()
            return

        self._append("user", text)
        self._clear_entry()

        try:
            resp = self.auto.step(text)
        except Exception as e:
            resp = f"[ERROR] {e}"
        self._append("bot", resp)
        self._refresh_state()


def run_gui() -> None:
    root = tk.Tk()
    # Estilo ttk por defecto
    try:
        root.call("tk", "scaling", 1.0)  # evita tamaños gigantes si hay HiDPI
    except Exception:
        pass
    _ChatGUI(root)
    root.mainloop()


# Permite ejecutar directo: `python -m utils.gui_tk`
if __name__ == "__main__":
    run_gui()


# =============================
# File: main.py (versión con GUI opcional)
# =============================
# from utils.automata import get_automata
# import sys
#
# def run_console():
#     auto = get_automata()
#     print("SAES CHAT listo. Escribe 'salir' para terminar.")
#     while True:
#         try:
#             user = input("> ")
#         except (EOFError, KeyboardInterrupt):
#             print("\nHasta luego.")
#             break
#         if user.strip().lower() in {"salir", "exit", "quit"}:
#             print("Hasta luego.")
#             break
#         resp = auto.step(user)
#         print(resp)
#
# def run_gui():
#     # Delega a la GUI Tkinter
#     from utils.gui_tk import run_gui as _run
#     _run()
#
# if __name__ == "__main__":
#     # Ejecuta GUI si pasas "--gui" o si prefieres por defecto
#     if "--gui" in sys.argv:
#         run_gui()
#     else:
#         # Cambia a run_gui() si quieres que la GUI sea el modo por defecto
#         run_console()
