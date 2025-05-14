# server.py
import socket
import threading
import sys
import os

class Server():


    FAKE_SERVER_IP = "10.10.1.1" # puedes ocultar la ip real para evitar ataques.

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.clients = {}      # puerto_cliente -> {'socket', 'alias', 'id'}
        self.next_id = 1       # contador para IDn y fake IP de clientes
        self._listen()
        self._accept_connections()

    def _listen(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR if os.name=='nt' else socket.SO_REUSEPORT,
                1
            )
            self.server.bind((self.ip, self.port))
            print(f'SERVIDOR: Escuchando en {self.FAKE_SERVER_IP}:{self.port}')
            self.server.listen(4)
        except Exception as e:
            print(f'SERVIDOR: Error al escuchar: {e}')
            self.server.close()
            sys.exit(1)

    def _accept_connections(self):
        try:
            while True:
                print('SERVIDOR: Esperando conexion…')
                client_sock, address = self.server.accept()
                client_port = address[1]
                client_id = self.next_id
                alias     = f"ID{client_id}"
                self.next_id += 1

                # Registramos cliente
                self.clients[client_port] = {
                    'socket': client_sock,
                    'alias':  alias,
                    'id':     client_id
                }

                fake_ip = f"10.10.1.{client_id}" #ocultar ip de clientes
                print(f'SERVIDOR: Cliente conectado ? {fake_ip}:{client_port} como {alias}')

                # Aviso de alias
                try:
                    client_sock.send(f"SERVER: Tu alias es {alias}".encode('utf-8'))
                except:
                    pass

                # Arranco handler en hilo
                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_port),
                    daemon=True
                )
                handler.start()
        except Exception as e:
            print(f'SERVIDOR: Error aceptando conexiones: {e}')

    def _handle_client(self, client, client_port):
        try:
            with client:
                while True:
                    data = client.recv(1024)
                    if not data:
                        break
                    text     = data.decode('utf-8').strip()
                    me       = self.clients.get(client_port)
                    if not me:
                        break
                    my_alias = me['alias']

                    # 1) /alias <nuevo_alias>
                    if text.startswith('/alias '):
                        nuevo = text[len('/alias '):].strip()
                        if nuevo:
                            old = me['alias']
                            me['alias'] = nuevo
                            client.send(f"SERVER: Alias {old} ? {nuevo}".encode('utf-8'))
                            print(f"SERVIDOR: {old} ({client_port}) ahora es {nuevo}")
                        else:
                            client.send(b"SERVER: Debes dar un alias valido.\n")
                        continue

                    # 2) /lista
                    if text == '/lista':
                        lineas = []
                        for port, info in self.clients.items():
                            fake_ip = f"10.10.1.{info['id']}"
                            lineas.append(f"{info['alias']} – {fake_ip}:{port}")
                        lista = "SERVER: Clientes:\n" + "\n".join(lineas)
                        client.send(lista.encode('utf-8'))
                        continue

                    # 3) /all <mensaje>
                    if text.startswith('/all '):
                        msg = text[len('/all '):].strip()
                        if not msg:
                            client.send(b"SERVER: Mensaje vacio.\n")
                            continue
                        payload = f"{my_alias} (all): {msg}"
                        for info in self.clients.values():
                            try:
                                info['socket'].send(payload.encode('utf-8'))
                            except:
                                pass
                        print(f"SERVIDOR: Broadcast {my_alias}: {msg}")
                        continue

                    # 4) Mensaje directo por puerto o alias
                    parts = text.split(' ', 1)
                    if len(parts) != 2:
                        client.send(b"SERVER: Formato invalido. Usa '<puerto|alias> mensaje'.\n")
                        continue

                    target, msg = parts
                    dest = None

                    # si es número, lo tratamos como puerto
                    if target.isdigit():
                        port = int(target)
                        dest = self.clients.get(port)
                    else:
                        # buscamos por alias
                        for info in self.clients.values():
                            if info['alias'] == target:
                                dest = info
                                break

                    if dest:
                        payload = f"{my_alias}: {msg}"
                        try:
                            dest['socket'].send(payload.encode('utf-8'))
                            print(f"SERVIDOR: {my_alias} ? {dest['alias']}: {msg}")
                        except:
                            client.send(b"SERVER: Error al enviar mensaje.\n")
                    else:
                        client.send(f"SERVER: Destino '{target}' no existe.\n".encode('utf-8'))

        except Exception as e:
            print(f"SERVIDOR: Error con cliente {client_port}: {e}")
        finally:
            if client_port in self.clients:
                alias = self.clients[client_port]['alias']
                print(f"SERVIDOR: {alias} ({client_port}) desconectado")
                del self.clients[client_port]

    def shutdown(self):
        for info in self.clients.values():
            try: info['socket'].close()
            except: pass
        self.server.close()


if __name__ == "__main__":
    Server("0.0.0.0", 2018)
