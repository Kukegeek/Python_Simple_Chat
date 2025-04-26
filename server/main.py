from server import Server            # Importa la clase Server definida arriba

def main():                          # Función principal del servidor
    Server("10.10.1.1", 2018)        # Instancia el servidor escuchando en 10.10.1.1:2018

if __name__ == "__main__":           # Ejecutar solo si el fichero se corre directamente
    main()                            # Llama a main()
