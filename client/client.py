# client.py
import socket
import threading
import sys

class Client():


    FAKE_SERVER_IP = "10.10.1.1"

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self._connect()
        threading.Thread(target=self._receive_messages, daemon=True).start()

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            self.local_port = self.sock.getsockname()[1]
            print(f'Conectado a {self.FAKE_SERVER_IP}:{self.port}  (mi puerto local {self.local_port})')
        except Exception as e:
            print(f'Error conexion: {e}')
            sys.exit(1)

    def send(self, text):
        try:
            self.sock.send(text.encode('utf-8'))
        except Exception as e:
            print(f'Error enviando: {e}')

    def _receive_messages(self):
        try:
            while True:
                data = self.sock.recv(1024)
                if not data:
                    print('\n[Desconectado]')
                    break
                print(f'\n?? Mensaje: {data.decode("utf-8")}\n>> ', end='', flush=True)
        except Exception as e:
            print(f'\nError recepcion: {e}')

    def close(self):
        try:
            self.sock.close()
        except:
            pass
