import socket
import threading
import sys
import os


class Server():

    def __init__(self, ip, port):

        self.ip = ip
        self.port = port
        self._listen(ip, port)
        self._accept_connection()

    # Listen for incoming connections
    def _listen(self, ip, port):

        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if os.name == 'nt':
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.server.bind((ip, port))
            print(f'Listening on IP Address: {ip} and Port: {port} ')
            self.server.listen(4)
        except Exception as e:
            print(f'Problem listening for incoming connection: {e}')
            self.server.close()
            sys.exit(0)

    # Accept incoming connection
    def _accept_connection(self):

        try:
            with self.server:
                while True:
                    print(f'Waiting for incoming client connection...')
                    client, address = self.server.accept()
                    print(f'Accepted client connection from IP Address: {address[0]} and {address[1]}')
                    client_handler = threading.Thread(target=self._process_client_requests, args=(client, self.server))
                    client_handler.start()
        except Exception as e:
            print(f'Problem accepting connection: {e}')

    # Process connection in separate thread
    def _process_client_requests(self, client, server):
                    # --- broadcast ---
                    if message.startswith('/all '):
                        payload = message[5:]
                        for p, (s, _, _) in self.clients.items():
                            if p != client_port:
                                s.send(
                                  f"{self.clients[client_port][2]} (a TODOS) ► {payload}"
                                  .encode()
                                )
                        continue
                    # --- who-am-I ---
                    if message.lower() == 'alias':
                        _, ip, alias = self.clients[client_port]
                        client.send(
                            f"Tu alias: {alias} IP:{ip} Port:{client_port}\\n".encode()
                        )
                        continue

                    # --- alias <nombre> ---
                    if message.lower().startswith('alias '):
                        nuevo = message.split(' ', 1)[1]
                        if nuevo in self.alias_map:
                            client.send(b'ERROR alias en uso\\n'); continue
                        self.alias_map.pop(self.clients[client_port][2], None)
                        self.alias_map[nuevo] = client_port
                        sock, ip, _ = self.clients[client_port]
                        self.clients[client_port] = (sock, ip, nuevo)
                        client.send(b'Alias cambiado\\n')
                        continue
        try:
            with client:
                while True:
                    request = client.recv(1024)
                    if not request:
                        break
                   message = request.decode('utf-8').strip()

                    # --- nuevo comando lista ---
                    if message.lower() == 'lista':
                        with self.lock:
                        ports = '\\n'.join(f"{ip}:{p}"
                            for p, (_, ip, _) in self.clients.items())
                        client.send(ports.encode())
                        continue

                    # --- routing: <puerto> <texto> ---
                    try:
                        dest_port, payload = message.split(' ', 1)
                        dest_port = int(dest_port)
                    except ValueError:
                        client.send(b'ERROR formato\\n')
                        continue

                    with self.lock:
                        dest_sock = self.clients.get(dest_port)
                    if dest_sock:
                        dest_sock.send(
                            f"{self.clients[client_port][2]} ► {payload}".encode()
                        )
                    else:
                       client.send(b'ERROR puerto no conectado\\n')

        except Exception as e:
            print(f'Problem processing client requests: {e}')
