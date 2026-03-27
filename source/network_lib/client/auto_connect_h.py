import asyncio
import aiohttp
import hashlib
from network_lib.client.auto_connect_client.auto_find_server import auto_find_server
from network_lib.client.auto_connect_client.save_server import save_server



from typing import Optional, Tuple

class auto_connect_h:
    def __init__(self):
        self.SERVER_FILE = (
            "C:\\Users\\jonas\\Desktop\\THREE GT\\3Dreamz-AutoPilot\\source\\server.json"
        )
        self.db = save_server(self.SERVER_FILE)
        self.scanner = auto_find_server()

    def getServer(self) -> tuple[str, int] | None:
        """Lädt gespeicherten Server aus JSON-Datei.
        Gibt (ip, hash) zurück oder None wenn nicht vorhanden."""
        data = self.db.load()
        if data == {} or data == None:
            return None
        ip = data.get("ipv4")
        port = data.get("port")
        if ip and port:
            return (ip, port)
        return None

    # ---------- Wrapper: Netzwerk-Requests ----------
    async def request_hash(self, ip: str, hash_param: str | None = None) -> str | None:
        """Sendet GET-Request mit optionalem Hash-Parameter."""
        url = f"http://{ip}/server_found.php?iq=169"
        if hash_param:
            url += f"&hash={hash_param}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=3) as resp:
                    body = await resp.read()
                    if not body:
                        return None
                    print(f"[i] Antwort von {ip}: {body.decode().strip()}")
                    return (body.decode().strip())
            except Exception:
                return "null"

    # ---------- Wrapper: Serverprüfung ----------
    async def check_existing_server(self, ip: str, stored_hash: str | None) -> tuple[str, str] | None:
        """Prüft, ob bekannter Server noch erreichbar ist.
        Gibt (port, hash) zurück oder None bei Fehler."""
        if not ip:
            return None

        print(f"[i] Prüfe bekannten Server {ip} ...")
        result = await self.request_hash(ip, stored_hash)
        

        if not result:
            print(f"[x] {ip} nicht erreichbar.")
            return None

        # PHP gibt z. B. "e4d909c290d0fb1ca068ffaddf22cbd0:1797" zurück
        if ":" not in result:
            print(f"[x] Ungültiges Antwortformat von {ip}: {result}")
            return None

        hash_part, port = result.split(":", 1)
        hash_part, port = hash_part.strip(), port.strip()

        if hash_part == stored_hash:
            print(f"[OK] Server {ip} bestätigt bestehenden Hash.")
        else:
            print(f"[!] Hash hat sich geändert ({stored_hash} → {hash_part}).")

        return (port, hash_part)


    # ---------- Wrapper: Neuen Server suchen ----------
    async def find_new_server(self) -> tuple[str, str] | None:
        """Startet Netzwerkscan, um neuen Server zu finden."""
        print("[i] Starte Netzwerkscan ...")
        found = await self.scanner.run()
        if not found:
            print("[x] Kein Server gefunden.")
            return None
        print(f"[+] Neuer Server gefunden: {found[0]}")
        return found

    # ---------- Wrapper: Datenbankoperationen ----------
    def save_server_data(self, ip: str, new_hash: str, port: int):
        """Überschreibt die gespeicherten Serverdaten vollständig."""
        
        data = {
            "ipv4": ip,
            "hash": new_hash,
            "port": port
        }

        self.db.update(data)
        print(f"[✓] Server gespeichert: {ip}:{port}")

    # ---------- Hauptablauf ----------
    async def run_auto_connect(self) -> Optional[Tuple[str, int]]:
        """Verbindet sich mit bekanntem Server oder scannt neu.
           Gibt (ip, hash) zurück oder None wenn nichts gefunden wurde."""
        self.db.ensure_file("default_hash")
        data = self.db.load()
        stored_ip = data.get("ipv4")
        stored_hash = data.get("hash")

        # 1️⃣ Versuch: bestehenden Server prüfen
        if stored_ip:
            result = await self.check_existing_server(stored_ip, stored_hash)
            if result is None:
                print("[!] Bekannter Server nicht erreichbar.")
            else:
                port = result[0]
                new_hash = result[1]
                if new_hash:
                    if new_hash != stored_hash:
                        self.save_server_data(stored_ip, new_hash, port)
                    return  (stored_ip, new_hash,port)   # <-- Tuple zurückgeben
                print("[!] Bekannter Server nicht erreichbar.")
        else:
            print("[i] Keine gespeicherte Server-IP gefunden.")

        # 2️⃣ Fallback: neuen Server scannen
        result = await self.find_new_server()  # sollte Optional[Tuple[str,str]] zurückgeben
        print(f"[i] Scan-Ergebnis: {result}")
    
        if not result:
            return None
        if result[2] == "null":
            print("[x] Kein gültiger Hash erhalten.")
            return None
        print(result)
        
        ip = result[0]
        new_hash = result[1]
        port = result[2]
        
        if new_hash:
            print("SAVING",ip, new_hash, port)
            self.save_server_data(ip, new_hash, port)
            return (ip,new_hash,port)   # <-- Tuple zurückgeben
        else:
            print("[x] Kein gültiger Hash erhalten.")
            return None