

# flow.py
# Zentrale Funktionsbibliothek für Server

# ============================================================
# SENDEN

def start_process(conn):
        """Sendet Startsignal an den Client."""
        try:
            conn.sendall(b"start_flow||")
            print("[FLOW → CLIENT] start_flow gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")

def choose_profile(conn, profile="s"):
        """Sendet choose_profile an den Client und wartet auf Ergebnis."""
        try:
            choose = f"choose_profile||{profile}"
            conn.sendall(choose.encode())
            print("[FLOW → CLIENT] Choosing profile now.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")

def start_setup(conn):
        """Sendet setup an den Client."""
        try:
            choose = f"setup||"
            conn.sendall(choose.encode())
            print("[FLOW → CLIENT] Preparing everything, waiting till setup has finished.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")

def requestBoxValues(conn):
        """Sendet getBoxValues an den Client."""
        try:
            choose = f"getBoxValues||"
            conn.sendall(choose.encode())
            print("[FLOW → CLIENT] Preparing everything, waiting till setup has finished.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")   


def sendCreateBox(conn, w, h):
        """Sends createBox with the found boundaries."""
        try:
            choose = f"createBox||{w}||{h}"
            conn.sendall(choose.encode())
            print("[FLOW → CLIENT] Preparing scan, waiting till success.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")   

def startScan(conn):
        """Sendet startScan an den Client."""
        try:
            conn.sendall(b"startScan||")
            print("[FLOW → CLIENT] startScan gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")

def waitForScanDone(conn):
        """Sendet waitForScanDone an den Client."""
        try:
            conn.sendall(b"waitForScanDone||")
            print("[FLOW → CLIENT] waitForScanDone gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")    


def exportScan(conn):
        """Sendet exportScan an den Client."""
        try:
            conn.sendall(b"exportScan||")
            print("[FLOW → CLIENT] exportScan gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")       



def done(conn):
        """Sendet done an den Client."""
        try:
            conn.sendall(b"done||")
            print("[FLOW → CLIENT] done gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")       





def ping_client(conn):
        """Sendet Ping an den Client."""
        try:
            conn.sendall(b"ping||")
            print("[FLOW → CLIENT] ping gesendet.")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")

def send_message(conn, text: str):
        """Sendet Nachricht an den Client."""
        try:
            packet = f"msg||{text}".encode()
            conn.sendall(packet)
            print(f"[FLOW → CLIENT] Nachricht gesendet: {text}")
        except Exception as e:
            print(f"[FLOW] Fehler beim Senden: {e}")




    # ============================================================
    # EMPFANGEN
    # ============================================================

def on_pong(conn):
        print("[FLOW ← CLIENT] Pong erhalten.")

def on_ready(conn):
        print("[FLOW ← CLIENT] Client ist bereit.")
        # Beispiel: automatisch start_Process senden
        start_process(conn)

def on_done(conn, msg):
        print("[FLOW ← CLIENT]" + msg)

def on_message(conn, msg):
        print(f"[FLOW ← CLIENT] Nachricht: {msg}")
