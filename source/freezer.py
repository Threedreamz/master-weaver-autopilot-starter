# freeze_resume.py
import psutil
from libs.pywinauto.process import winWerth_Process


def _get_pid_by_name(process_name="WinWerth.exe"):
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"].lower() == process_name.lower():
            return proc.info["pid"]
    return None


def freeze_resume(wp, command):
    try:
        pid = getattr(wp, "process_id", None) or getattr(wp, "pid", None)
        if pid is None:
            pid = _get_pid_by_name("WinWerth.exe")
        if pid is None:
            print("❌ PID konnte nicht ermittelt werden.")
            return

        proc = psutil.Process(pid)

        if command == "freeze":
            proc.suspend()
            print(f"✅ Prozess [{pid}] eingefroren.")
        elif command == "resume":
            proc.resume()
            print(f"✅ Prozess [{pid}] fortgesetzt.")
        else:
            print(f"❌ Unbekannter Befehl: '{command}' → Nutze 'freeze' oder 'resume'")

    except psutil.NoSuchProcess:
        print("❌ Prozess nicht gefunden.")
    except psutil.AccessDenied:
        print("❌ Zugriff verweigert – starte das Skript als Administrator.")
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    wp = winWerth_Process()
    wp.init()

    while True:
        command = input("\nBefehl eingeben (freeze / resume / exit): ").strip().lower()
        if command == "exit":
            print("👋 Beendet.")
            break
        freeze_resume(wp, command)