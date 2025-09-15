from utils.automata import get_automata

def run_console():
    auto = get_automata()
    print("SAES CHAT listo. Escribe 'salir' para terminar.")
    while True:
        try:
            user = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break
        if user.strip().lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        resp = auto.step(user)
        print(resp)

if __name__ == "__main__":
    run_console()
