import socket
import threading
import sys
import network_lib.server.flow as flow
from trello.trello import trello

from pi_autopilot.cam_interface.cam_py import cam_py
from network_lib.middleman.middleman import middleman


class Server:
    def __init__(self, host="0.0.0.0", port=1797):
        self.HOST = host
        self.PORT = port
        self.server_running = True
        self.active_conn = None

        self.server_socket = None
        self.fl = flow
        self.tr = trello()

        # Instances
        self.campy = cam_py()
        self.mm = middleman()

        # Threads
        self.cam_thread = None
        self.mm_thread = None

    # ============================================================
    # START background threads (new)
    # ============================================================
    def start_background_threads(self):
        """Startet CamPy und Middleman automatisch in eigenen Threads."""

        # ---- CAM THREAD ----
        def cam_runner():
            try:
                print("[THREAD] cam_py wird gestartet...")
                self.campy.start(True)
            except Exception as e:
                print(f"[THREAD] cam_py Fehler: {e}")

        self.cam_thread = threading.Thread(target=cam_runner, daemon=True)
        self.cam_thread.start()

        # ---- MIDDLEMAN THREAD ----
        def mm_runner():
            try:
                print("[THREAD] Middleman wird gestartet...")
                self.mm.start()
            except Exception as e:
                print(f"[THREAD] middleman Fehler: {e}")

        self.mm_thread = threading.Thread(target=mm_runner, daemon=True)
        self.mm_thread.start()

    # ============================================================
    # CLIENT HANDLER
    # ============================================================
    def client_handler(self, conn, addr):
        self.active_conn = conn
        print(f"[+] Client verbunden: {addr}")
        running = True

        def recv_loop():
            nonlocal running
            while running:
                try:
                    auftr = self.tr.getAuftrag()
                    aid = ""
                    # deine komplette Trello + Flow Logic bleibt unverändert
                    if not (self.tr.getAuftrag() == None):
                        aid = auftr['id']
                        if self.tr.getAuftragStatus() == "X":
                            self.tr.setState("start_flow")
                            flow.start_process(conn=conn)
                        if self.tr.getAuftragStatus() == "start_":
                            pass
                        if self.tr.getAuftragStatus() == "abort":
                            self.tr.moveToDefect(self.tr.getAuftrag()['id'])
                    else:
                        print("Kein Auftrag vorhanden.")

                    data = conn.recv(1024)
                    if not data:
                        print("[-] Client getrennt.")
                        break
                   
                    decoded = data.decode().strip().replace("ping||", "")
                    parts = decoded.split("||")
                    
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    if len(decoded)>1:
                        print(f"parts{parts}")
                        print(f"decoded: {decoded}")
                    match command:
                        case "get_profile":
                            print("Requesting Profile from client.")
                            profile = self.tr.getProfile()
                            flow.choose_profile(conn, profile)
                        case "success:1":
                            self.tr.makeComment(aid, "success:1")
                            print("Administrating setup to client.")
                            flow.start_setup(conn)

                        case "success:2":
                            self.tr.makeComment(aid, "success:2")
                            print("Setup success. Waiting for Box Values")
                            flow.requestBoxValues(conn)
                        case "success:3":
                            self.tr.makeComment(aid, "success:3")
                            print("Values are ".join(args))
                            flow.sendCreateBox(conn,parts[1], parts[2])
                        case "success:4":
                            self.tr.makeComment(aid, "success:4")
                            flow.startScan(conn)
                        case "success:5":
                            self.tr.makeComment(aid, "success:5")
                            flow.waitForScanDone(conn)
                        case "success:6":
                            self.tr.makeComment(aid, "success:6")
                            flow.exportScan(conn)
                        case "success:7":
                            self.tr.makeComment(aid, "Complete")
                            flow.done(conn)
                        case _:
                            pass

                except:
                    break

            running = False
            conn.close()
            self.active_conn = None
            print("[*] Warten auf neuen Client ...")

        threading.Thread(target=recv_loop, daemon=True).start()

    # ============================================================
    # SERVER INPUT LOOP
    # ============================================================
    def helpOutput(self):
        print("start cam")
        print("stop cam")
        print("r cam - restarts cam")

    def server_input_loop(self):
        while self.server_running:
            try:
                cmd = input("Server > ").strip()

                if cmd == "start cam":
                    threading.Thread(target=self.campy.start, args=(True,), daemon=True).start()

                if cmd == "stop cam":
                    self.campy.stop()

                if cmd == "start api":
                    threading.Thread(target=self.mm.start, daemon=True).start()

                if cmd == "":
                    continue

                if cmd == "exit":
                    print("[SERVER] Gesamter Server wird beendet.")
                    self.stop_server()
                    sys.exit(0)

                if not self.active_conn:
                    print("[SERVER] Kein Client verbunden.")
                    continue

                if cmd == "quit":
                    try:
                        self.active_conn.shutdown(socket.SHUT_RDWR)
                        self.active_conn.close()
                    except:
                        pass
                    self.active_conn = None

                elif cmd == "start":
                    flow.start_process(self.active_conn)

                elif cmd == "ping":
                    flow.ping_client(self.active_conn)

                elif cmd == "start_rec":
                    flow.choose_profile(self.active_conn)

                elif cmd.startswith("msg "):
                    text = cmd[4:].strip()
                    flow.send_message(self.active_conn, text)

                else:
                    print("[SERVER] Unbekannter Befehl.")

            except KeyboardInterrupt:
                print("\n[SERVER] Manuell beendet.")
                self.stop_server()
                sys.exit(0)

    # ============================================================
    # START SERVER
    # ============================================================
    def start_server(self):
        self.start_background_threads()   # <----- HIER WERDEN SIE AUTOMATISCH GESTARTET

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(1)
        print(f"[*] Server läuft auf {self.HOST}:{self.PORT}")

        threading.Thread(target=self.server_input_loop, daemon=True).start()

        while self.server_running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.client_handler, args=(conn, addr)).start()
            except:
                break

        print("[SERVER] Beendet.")

    # ============================================================
    # STOP SERVER
    # ============================================================
    def stop_server(self):
        self.server_running = False
        try:
            if self.active_conn:
                self.active_conn.close()
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        print("[SERVER] Socket geschlossen.")
