import socket
import threading
import time
import sys

from libs.pseudo_pipe.pywin_pipe import pywin_pipe
from auto_connect import auto_connect
from trello.trello import trello


class Client:
    def __init__(self, host="192.168.2.3", port=1797):
        self.running = True
        self.sock = None

        self.tr = trello()
        self.auto_con = auto_connect()
        self.pipe = pywin_pipe()

        server_json = self.auto_con.getServer()
        if server_json is not None:
            self.HOST = server_json[0]
            self.PORT = server_json[1]
        else:
            self.HOST = host
            self.PORT = port

        print(f"[CLIENT] → Initialisiere Client für {self.HOST}:{self.PORT}...")

    def auto_connect(self):
        try:
            return self.auto_con.connect_client()
        except Exception as e:
            print(f"[AUTO CONNECT] Fehler: {e}")

    def start_Process(self):
        print("[CLIENT] → start_Process empfangen.")
        time.sleep(1)
        self.send_done()

    def send_done(self):
        try:
            self.sock.sendall(b"start_rec||0")
        except:
            pass

    def send_ready(self):
        try:
            self.sock.sendall(b"ready||0")
            print("[CLIENT] → Ready gesendet.")
        except:
            pass

    # ============================================================
    # PING LOOP — sendet regelmäßig Ping
    # ============================================================
    def ping_loop(self):
        while self.running:
            try:
                self.sock.sendall(b"ping||")
                print("[CLIENT] → Ping gesendet.")
            except Exception as e:
                print(f"[CLIENT] Ping-Fehler: {e}")
                break
            time.sleep(10)  # alle 10 Sekunden

    # ============================================================
    # RECV LOOP
    # ============================================================
    def recv_loop(self):
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    print("[CLIENT] Verbindung getrennt.")
                    return "-1"

                decoded = data.decode().strip()
                parts = decoded.split("||")
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                print(f"parts: {parts}")
                match command:
                    case "start":
                        print("starting initiated")
                    case "start_flow":
                        self.sock.sendall(b"get_profile||")
                        print("Started Process")
                    case "choose_profile":
                        print(f"[CLIENT] Profil wählen: {' '.join(parts[1])}")
                        #self.pipe.selectProfile(parts[1])
                        #self.pipe.choose_profile(parts[1])
                        self.sock.sendall(b"success:1||")
                    case "setup":
                        print(f"[CLIENT] setup started")
                        #self.pipe.setup()
                        #self.pipe.checkLiveBild()
                        self.sock.sendall(b"success:2||")
                        print("Returned success:2")
                    case "getBoxValues":
                        print(f"[CLIENT] prep scan now, gathering geometric data... ")
                        #values = self.pipe.getBoxValues()
                        #msg = f"success:3||{values[0]}||{values[1]}"
                        msg = "success:3||2||2"
                        self.sock.sendall(msg.encode())

                    case "createBox":
                        print(f"[CLIENT] creating box now... ")
                        #self.pipe.createBox()
                        self.sock.sendall(b"success:4||")
                    case "startScan":
                        print(f"[CLIENT] starting scan... ")
                        #self.pipe.startScan()
                        self.sock.sendall(b"success:5||")
                    case "waitForScanDone":
                        print(f"[CLIENT] waiting for scan to finish... ")
                        #self.pipe.waitForScanDone()
                        self.sock.sendall(b"success:6||")
                    case "exportScan":
                        print(f"[CLIENT] exporting scan... ")
                        #self.pipe.exportScan()
                        self.sock.sendall(b"success:7||")
                    case "done":
                        print("Scan successfully completed!")
                    case "ping":
                        self.sock.sendall(b"pong||")
                        print("[CLIENT] → Pong gesendet.")
                    case "start_Process":
                        self.start_Process()
                        print("Started Process")
                    case "msg":
                        print(f"[SERVER] Nachricht: {' '.join(args)}")
                    case _:
                        print(f"[CLIENT] Unbekanntes Paket: {decoded}")

            except (ConnectionResetError, OSError):
                print("[CLIENT] Verbindung verloren.")
                return "-1"
            except Exception as e:
                print(f"[CLIENT] Fehler: {e}")
                return "-2"

        self.running = False
        return "0"

    # ============================================================
    # INPUT LOOP
    # ============================================================
    def input_loop(self):
        while self.running:
            try:
                msg = input("Client > ").strip()
                if msg == "":
                    continue
                elif msg == "exit":
                    print("[CLIENT] Beende Programm.")
                    self.running = False
                    try:
                        self.sock.shutdown(socket.SHUT_RDWR)
                        self.sock.close()
                    except:
                        pass
                    sys.exit(0)
                elif msg == "quit":
                    print("[CLIENT] Verbindung getrennt.")
                    try:
                        self.sock.shutdown(socket.SHUT_RDWR)
                        self.sock.close()
                    except:
                        pass
                    return
                elif msg == "ready":
                    self.send_ready()
                elif msg.startswith("msg "):
                    text = msg[4:].strip()
                    packet = f"msg||{text}".encode()
                    self.sock.sendall(packet)
                    print(f"[CLIENT] → Nachricht gesendet: {text}")
                else:
                    print("[CLIENT] Unbekannter Befehl.")
            except KeyboardInterrupt:
                print("\n[CLIENT] Manuell beendet.")
                sys.exit(0)
            except Exception as e:
                print(f"[CLIENT] Eingabefehler: {e}")
                return

    # ============================================================
    # MAIN LOOP mit Reconnect-Logik
    # ============================================================
    def start_client(self):
        autoconnected = True
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.HOST, int(self.PORT)))
                print("[CLIENT] Erfolgreich verbunden!")

                # Ping-Thread starten
                ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
                ping_thread.start()

                # Empfangen (blockierend)
                recv_result = self.recv_loop()

                # Verbindung schließen
                try:
                    self.sock.close()
                except:
                    pass

                if recv_result == "-2":
                    print("[CLIENT] Schwerer Fehler – Programm wird beendet.")
                    break
                elif recv_result == "-1":
                    print("[CLIENT] Versuche erneut zu verbinden in 3s...")
                    time.sleep(3)
                    continue
                else:
                    print("[CLIENT] Verbindung normal beendet.")
                    break

            except ConnectionRefusedError:
                if autoconnected:
                    print("[CLIENT] Server nicht erreichbar, versuche autoconnect in 3s...")
                    time.sleep(3)
                    connection_info = self.auto_connect()
                    print("CONNECTION INFO :", connection_info)
                    self.HOST = connection_info[0]
                    self.PORT = int(connection_info[1])
                    autoconnected = False
                else:
                    print("[CLIENT] Server nicht erreichbar und autoconnect erfolglos.")
                    print(f"[CLIENT] found\nSERVER IP : {self.HOST} , PORT : {self.PORT}")
                    time.sleep(3)
            except KeyboardInterrupt:
                print("\n[CLIENT] Manuell beendet.")
                break
            except Exception as e:
                print(f"[CLIENT] Fehler: {e}")
                print("[CLIENT] Server nicht erreichbar, versuche autoconnect in 3s...")
                time.sleep(3)
                connection_info = self.auto_connect()
                print("CONNECTION INFO :", connection_info)
                self.HOST = connection_info[0]
                self.PORT = int(connection_info[1])
                autoconnected = False
                time.sleep(3)
