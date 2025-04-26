import socket                      # Biblioteca estándar de sockets TCP/IP
import threading                   # Biblioteca para hilos ligeros (threading)
from typing import Dict, Tuple     # Tipado opcional (Dict, Tuple)

class Server:                      # Definición de la clase Server
    # Clase principal que implementa el servidor de chat.

    # ---------------------------
    # Constructor
    # ---------------------------
    def __init__(self, ip: str, port: int):          # IP/puerto donde escuchar
        # Mapa de clientes conectados: {puerto_cliente: (socket, ip_cliente, alias)}
        self.clients: Dict[int, Tuple[socket.socket, str, str]] = {}
        # Mapa de alias a puerto: {alias: puerto_cliente}
        self.alias_map: Dict[str, int] = {}
        # Último destino usado por cliente: {puerto_origen: puerto_destino}
        self.last_dest: Dict[int, int] = {}
        self.next_alias_id = 1                       # Contador para alias automáticos
        self.lock = threading.Lock()                 # Mutex para secciones críticas

        # --- Creación del socket de escucha ---
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket TCP
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reusar puerto rápido
        self.server.bind((ip, port))                 # Asocia IP/puerto al socket
        self.server.listen(8)                        # Empieza a escuchar (máx 8 en cola)
        print(f"Listening on {ip}:{port}")           # Mensaje de log
        self._accept_loop()                          # Inicia bucle de aceptación

    # ---------------------------
    # Bucle de aceptación de clientes
    # ---------------------------
    def _accept_loop(self):
        with self.server:                            # Garantiza cierre al salir
            while True:                              # Bucle infinito
                client, (addr_ip, addr_port) = self.server.accept()  # Espera conexión
                # -- Registro del cliente --
                with self.lock:                      # Entra en región crítica
                    alias = f"ID{self.next_alias_id}" # Crea alias automático
                    self.next_alias_id += 1
                    self.clients[addr_port] = (client, addr_ip, alias) # Guarda datos
                    self.alias_map[alias] = addr_port                 # Alias→puerto
                print(f"Accepted {addr_ip}:{addr_port} as {alias}")
                # Crea un hilo por cliente
                threading.Thread(target=self._handle_client,
                                 args=(client, addr_port), daemon=True).start()

    # ---------------------------
    # Manejo de un solo cliente (cada hilo)
    # ---------------------------
    def _handle_client(self, client: socket.socket, origin_port: int):
        try:
            with client:                             # Auto‑cierre al salir
                while True:                          # Bucle de lectura
                    data = client.recv(4096)         # Lee hasta 4 KiB
                    if not data:                     # Si recv()==b'' => desconexión
                        break
                    raw = data.decode().strip()      # Decodifica a str, quita espacios
                    lower_raw = raw.lower()          # Versión minúsculas para comparar

                    # --- Comando «alias» sin argumento: who‑am‑I ---
                    if lower_raw == "alias":
                        self._whoami(client, origin_port)
                        continue
                    # --- Comando lista ---
                    if lower_raw == "lista":
                        self._send_list(client)
                        continue
                    # --- Comando alias <nombre> (cambio de alias) ---
                    if lower_raw.startswith("alias "):
                        self._change_alias(client, origin_port, raw)
                        continue
                    # --- Broadcast /all <mensaje> ---
                    if lower_raw.startswith("/all "):
                        self._broadcast(origin_port, raw[5:].lstrip())
                        continue

                    # --- Posible mensaje dirigido ---
                    parts = raw.split(" ", 1)       # Separa primera palabra
                    if len(parts) == 2:              # Si hay destino explícito
                        dest_token, message = parts  # dest_token = puerto|alias
                        # Reenvía y guarda como último destino
                        if self._route_message(origin_port, dest_token, message):
                            self._remember_dest(origin_port, dest_token)
                        else:
                            client.sendall(b"ERROR: destino desconocido\n")
                        continue
                    # --- Mensaje sin destino explícito ---
                    else:
                        if self._send_to_last(origin_port, raw):  # Usa último destino si existe
                            continue
                        client.sendall(b"ERROR: especifica <puerto|alias> primero. Usa 'lista'\n")
        finally:
            self._disconnect(origin_port)            # Limpia al desconectar

    # ---------------------------
    # Funciones auxiliares privadas (_)
    # ---------------------------
    def _whoami(self, sock: socket.socket, port: int):
        # Envía al cliente sus propios datos (alias, IP y puerto).
        with self.lock:
            _, ip, alias = self.clients[port]
        sock.sendall(f"Tu alias: {alias}  Puerto: {port}  IP: {ip}\n".encode())

    def _send_list(self, sock: socket.socket):
        # Envía lista de todos los clientes conectados.
        with self.lock:
            lines = [f"{ip}:{p} {a}" for p, (_, ip, a) in self.clients.items()]
        sock.sendall(("\n".join(lines)+"\n").encode())

    def _change_alias(self, sock: socket.socket, port: int, raw: str):
        # Cambia alias de un cliente, comprobando colisiones.
        new_alias = raw.split(" ",1)[1].strip().strip('"') # Obtiene el nombre deseado
        if not new_alias:
            sock.sendall(b"ERROR: alias vacio\n"); return
        with self.lock:
            if new_alias in self.alias_map and self.alias_map[new_alias]!=port:
                sock.sendall(b"ERROR: alias ya en uso\n"); return
            sock_obj, ip, old_alias = self.clients[port]
            if old_alias:
                self.alias_map.pop(old_alias, None)         # Elimina alias viejo
            self.alias_map[new_alias] = port                # Registra alias nuevo
            self.clients[port] = (sock_obj, ip, new_alias)  # Actualiza tupla
        sock.sendall(f"Alias cambiado a {new_alias}\n".encode())

    def _broadcast(self, sender_port: int, msg: str):
        # Envía un mensaje a todos menos al remitente.
        with self.lock:
            sender_alias = self.clients[sender_port][2]     # Alias emisor
            targets = [sock for p,(sock,_,_) in self.clients.items() if p!=sender_port]
        payload = f"{sender_alias} (a TODOS) ► {msg}".encode()
        for s in targets:
            try:
                s.sendall(payload)
            except:
                pass  # Ignora fallos puntuales

    def _route_message(self, origin_port: int, dest_token: str, message: str) -> bool:
        # Reenvía `message` al destino si existe. Devuelve True si se entregó.
        with self.lock:
            dest_port = int(dest_token) if dest_token.isdigit() else self.alias_map.get(dest_token)
            dest_entry = self.clients.get(dest_port) if dest_port else None
        if dest_entry:
            self._send_to(dest_entry[0], origin_port, message)
            return True
        return False

    def _remember_dest(self, origin_port: int, dest_token: str):
        # Guarda el destino como último para mensajes futuros sin destino.
        with self.lock:
            dest_port = int(dest_token) if dest_token.isdigit() else self.alias_map.get(dest_token)
            if dest_port:
                self.last_dest[origin_port] = dest_port

    def _send_to_last(self, origin_port: int, message: str) -> bool:
        # Intenta enviar al último destino almacenado.
        dest_port = self.last_dest.get(origin_port)
        if not dest_port:
            return False
        with self.lock:
            dest_entry = self.clients.get(dest_port)
        if dest_entry:
            self._send_to(dest_entry[0], origin_port, message)
            return True
        return False

    def _send_to(self, dest_sock: socket.socket, sender_port: int, msg: str):
        # Enriquece el mensaje con alias del remitente y lo envía.
        with self.lock:
            sender_alias = self.clients[sender_port][2]
        payload = f"{sender_alias} ► {msg}".encode()
        try:
            dest_sock.sendall(payload)
        except Exception as e:
            print("Error enviando:", e)

    def _disconnect(self, port: int):
        # Elimina todas las referencias de un cliente desconectado.
        with self.lock:
            entry = self.clients.pop(port, None)
            if entry:
                _, _, alias = entry
                self.alias_map.pop(alias, None)
                self.last_dest.pop(port, None)
        print(f"Client {port} disconnected")
