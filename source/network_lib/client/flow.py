# source/network_lib/server/overlord.py
import flow

class Overlord:
    def receive(self, command, args, conn):
        """Verarbeitet eingehende Befehle vom Client."""
        match command:
            case "pong":
                flow.on_pong(conn)
            case "ready":
                flow.on_ready(conn)
            case "done":
                flow.on_done(conn)
            case "msg":
                msg = " ".join(args)
                flow.on_message(conn, msg)
            case _:
                print(f"[Overlord] Unbekannter Befehl: {command}")
