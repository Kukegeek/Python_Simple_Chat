import socket                     # Biblioteca de sockets TCP

class Client:                     # Implementa un cliente simple de consola

    # Constructor: establece la conexión con el servidor
    def __init__(self, ip: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Crea socket TCP
        self.sock.connect((ip, port))                                   # Conecta al servidor
        print(f"Conectado a {ip}:{port}")                               # Mensaje de confirmación

    # Envía una línea al servidor y espera posible respuesta
    def send(self, line: str):
        self.sock.send(line.encode())   # Convierte la línea a bytes UTF‑8 y la envía
        self._recv()                    # Llama a recepción inmediata (bloqueante corta)

    # Recibe datos pendientes del servidor (si los hay) y los muestra
    def _recv(self):
        try:
            data = self.sock.recv(4096) # Lee hasta 4 KiB (bloquea hasta que hay datos o se cierra)
            if data:
                print(data.decode())    # Muestra la respuesta en consola
        except:                        # Captura cualquier excepción de recv()
            pass                       # Ignora (podría no haber datos disponibles)

    # Cierra el socket de forma ordenada
    def close(self):
        self.sock.close()               # Cierra la conexión TCP
