from client import Client             # Importa la clase Client

def main():
    c = Client("10.10.1.1", 2018)    # Crea cliente y conecta al servidor
    print("Comandos: <destino> msg | /all msg | lista | alias [nombre] | quit")
    while True:                       # Bucle principal de lectura de teclado
        line = input("> ").strip()  # Lee la línea del usuario
        if not line:                  # Si está vacía, pedir de nuevo
            continue
        if line.lower() == "quit":   # Si es 'quit', cerrar y salir
            c.close()
            break
        c.send(line)                  # Envía la línea tal cual al servidor

if __name__ == "__main__":           # Ejecutar solo si se corre directamente
    main()                            # Llama a main()

